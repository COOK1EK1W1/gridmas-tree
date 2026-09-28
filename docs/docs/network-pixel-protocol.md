# Network pixel protocol

The wire protocol between the network_driver (the client) and a device 
(`device/ws2812/`, `device/pygame/`, `device/pico/` - the servers). 
Every device type implements this independently - see each device's 
own docs for implementation notes; this page is the shared spec
they all have to agree on.

The protocol is split across two transports:

- **Control plane - HTTP.** Low-frequency, want-a-reliable-response calls:
  `GET /status`, `POST /clear`.
- **Data plane - WebSocket.** The per-frame hot path, plus the device's
  readiness signal that rides alongside it. One WS connection per
  driver, used bidirectionally: the driver sends frame data on
  it, and the device replies with credit updates telling the driver how
  much more it can send. Only one driver connects to a device at a
  time - a new connection replaces whatever was there before.

Both share one TCP port on the device (8420 by default). Every connection
starts as HTTP; a `GET` carrying the WebSocket upgrade headers
(`Sec-WebSocket-Key` etc.) is answered with `101 Switching Protocols` and
carries WS messages from then on, while any other request is served as plain
HTTP.

## Control plane (HTTP)

### `GET /status`

Returns device/queue diagnostics. Response body:

```json
{
  "device_name": "pi1",
  "pixel_count": 500,
  "firmware_version": "1.0.0",
  "uptime_s": 123.4,
  "clock": 1234567890.123456,
  "queue": {"depth": 12, "capacity": 90},
  "stats": {
    "frames_received": 1000,
    "frames_shown": 980,
    "frames_dropped_late": 5,
    "frames_dropped_queue_full": 15
  }
}
```

`stats` fields are cumulative since boot/start.

### `POST /clear`

Drops every buffered frame and blanks the strip. No body. `200 OK` with an
empty body.

## Data plane (WebSocket)

The NetworkDriver is the WS client; the device is the WS server. All multi-byte
integers are big-endian. 
Every WS message is binary and starts with a 1-byte type tag:

```
type 0x01 = FRAME
type 0x02 = CREDIT
```

### FRAME message (driver -> device)

```
offset  size  field
0       1     type = 0x01
1       4     seq                  (uint32) - increments once per generated frame
5       8     presentation_time_us (int64) - unix epoch, microseconds; the
                                    wall-clock time this frame should be shown at
13      N     payload              - pixel_count * 3 bytes of RGB triples, in pixel order
```

A WS message carries the whole frame - there's no chunking. A frame at the
baseline 500-pixel tree is 1500 bytes of payload; a two-strip Pico fixture
can be up to 3000 bytes. WS's own message framing (backed by TCP) handles
this transparently.

### CREDIT message (device -> driver)

```
offset  size  field
0       1     type = 0x02
1       4     free_slots (uint32) - how many more frames the device can currently buffer
```

`free_slots` "how much room I have right now". This makes it
self-correcting: a delayed or coalesced TCP segment just means the
driver's view of the device's capacity is briefly stale, not
permanently wrong, since the next snapshot supersedes it rather than
compounding an error.

The device sends a CREDIT message:

- immediately once the WS handshake completes, before receiving any FRAME
  message,
- any time `free_slots` changes (a frame arrived, or a buffered frame was
  played or dropped), and
- on a periodic heartbeat, even if unchanged - so silence on the
  connection is itself meaningful (the driver treats a connection with
  no messages for several heartbeat intervals as dead and reconnects).

## Flow control

- A fresh or freshly-reconnected driver connection starts at zero
  credit and sends nothing until the device's first CREDIT snapshot
  arrives - there's no assumed default capacity.
- The driver tracks its own copy of the device's credit, decrementing
  it by one for each FRAME it sends and topping it back up whenever a new
  CREDIT snapshot arrives. It only sends while its local credit is above
  zero; a send with no credit available blocks (rather than sending
  anyway) until the device reports more room.
- The device's completed-frame buffer can still, in principle, be
  submitted into past capacity (e.g. a `/clear` or a mis-set buffer size) -
  submitting past capacity evicts the earliest-due slot rather than
  declining the new one. In practice, correct credit accounting on the driver 
  side means this should never actually trigger.
- The driver does not explicitly discard frames queued while
  disconnected or mid-reconnect. Instead, every frame is checked against
  its presentation time immediately before it would be sent; anything more
  than `LATE_GRACE_S` past due is dropped there, whether that lateness
  came from a slow network, a slow device, or time spent waiting to
  reconnect. This is a more accurate staleness test than "which connection
  was this queued during".

## Buffering and lateness

Frames should be buffered on the device, and displayed at the specified time.
If a frame is late by some amount of gace time, it should be discarded.
