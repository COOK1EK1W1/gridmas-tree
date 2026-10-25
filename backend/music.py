"""Play a song alongside a pattern or display, starting exactly on its first frame.

Call set_music() at the top of a pattern or display file (outside draw() / display_update()).
The song starts at the show epoch T0, the moment the first frame is displayed, and
seconds()/millis() inside the pattern are in step with it.

Audio is only played on the controller, and only when main.py is given --audio-device.
In the web editor set_music() does nothing.
"""

import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional, Union

import numpy as np

_IN_BROWSER = sys.platform == "emscripten"


@dataclass
class Song:
    samples: np.ndarray
    """int16 audio, shape (frames, channels)"""
    samplerate: int
    name: str

    @property
    def channels(self) -> int:
        return self.samples.shape[1]

    @property
    def duration(self) -> float:
        """Length of the song in seconds"""
        return len(self.samples) / self.samplerate


_pending: Optional[Song] = None
_requested = False


def set_music(source: Union[str, np.ndarray], samplerate: Optional[int] = None):
    """Play a song with this pattern, starting on the first frame

    Call this once, at the top of your pattern or display file. The song plays once
    and does not loop; the pattern keeps running after it ends. Use seconds() or
    millis() to time things against the song.

    Args:
        source (str | np.ndarray): Path to an audio file (wav, flac, ogg or mp3), relative to
            the file calling set_music(). Or an array of samples, shape (frames,) or (frames, channels),
            int16 or float in -1 to 1.
        samplerate (int, optional): Samples per second, required when source is an array.

    Example:
        ```
        set_music("harderstronger.mp3")

        def draw():
            if seconds() >= 12:
                fill(Color.red())
        ```
    """
    global _pending, _requested
    if _requested:
        raise ValueError("set_music() can only be called once per pattern")
    _requested = True

    if isinstance(source, np.ndarray):
        if samplerate is None:
            raise ValueError("set_music() needs a samplerate when given an array of samples")
        _pending = Song(_to_int16(source), samplerate, "<generated>")
        return

    caller_file = sys._getframe(1).f_globals.get("__file__")
    path = source
    if not os.path.isabs(path) and caller_file is not None:
        path = os.path.join(os.path.dirname(os.path.abspath(caller_file)), path)

    if _IN_BROWSER:
        print(f"set_music({source!r}): music is only played on the tree")
        return

    if not os.path.isfile(path):
        raise FileNotFoundError(f"set_music(): no audio file at {path}")
    try:
        import soundfile
    except ImportError as e:
        raise ImportError("set_music() needs the soundfile package: pip install soundfile") from e

    samples, rate = soundfile.read(path, dtype="int16", always_2d=True)
    _pending = Song(samples, rate, os.path.basename(path))


def _to_int16(samples: np.ndarray) -> np.ndarray:
    if samples.ndim == 1:
        samples = samples[:, None]
    if samples.dtype == np.int16:
        return np.ascontiguousarray(samples)
    return (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)


def _take_pending() -> Optional[Song]:
    """For internal use. The song requested by the pattern that just loaded, clearing the request"""
    global _pending, _requested
    song = _pending
    _pending = None
    _requested = False
    return song


def _clear_pending():
    _take_pending()


def list_devices():
    """Print the audio output devices PortAudio can see"""
    import sounddevice as sd
    print(sd.query_devices())


class AudioPlayer:
    """Plays a Song so its first sample leaves the DAC at T0 + offset.

    PortAudio reports, for every buffer it asks for, when that buffer will reach
    the DAC. The player compares that against where in the song it should be,
    outputting silence until T0 and then starting on the exact sample.

    During playback the sound card's clock drifts against the controller's
    clock (which the LEDs follow). Once the smoothed error passes
    DRIFT_THRESHOLD_S the player resamples by SLEW_RATE (inaudible) until it's
    back under DRIFT_SETTLED_S. Errors past RESYNC_THRESHOLD_S (an offset change
    or a stall) are fixed by jumping straight to the right sample.
    """

    DRIFT_THRESHOLD_S = 0.005
    DRIFT_SETTLED_S = 0.001
    RESYNC_THRESHOLD_S = 0.05
    SLEW_RATE = 0.002
    ERROR_SMOOTHING = 0.05
    WALL_OFFSET_RISE = 0.01
    FADE_S = 0.02

    def __init__(self):
        self.enabled = False
        self._device: Union[int, str, None] = None
        self.offset_s = 0.0

        self._stream = None
        self._song: Optional[Song] = None
        self._t0 = 0.0
        self._done = threading.Event()
        self._reset_playback_state()

    def configure(self, device: Optional[str], offset_ms: float = 0):
        """Set the output device.

        Args:
            device: None to disable audio, "default" for the system default output,
                otherwise a PortAudio device index or name.
            offset_ms: Positive values play the audio later relative to the lights.
        """
        self.enabled = device is not None
        self.offset_s = offset_ms / 1000
        if device is None or device == "default":
            self._device = None
        elif device.isdigit():
            self._device = int(device)
        else:
            self._device = device

    def set_offset_ms(self, offset_ms: float):
        """Change the audio offset, applied to the playing song straight away"""
        self.offset_s = offset_ms / 1000

    def _reset_playback_state(self):
        self._pos: Optional[float] = None
        self._wall_offset: Optional[float] = None
        self._error = 0.0
        self._correcting = False
        self._fading = False
        self._fade_remaining = 0
        self._finished = False
        # drift since the reference point: how far the smoothed error has moved,
        # plus the correction already applied to hold it in place
        self._ref_wall = 0.0
        self._ref_error = 0.0
        self._corrected = 0.0
        self._last_dac_wall = 0.0
        self._resyncs = 0
        self._underflows = 0
        self._drift_logged = False

    def play(self, song: Song, t0: float):
        """Stop whatever is playing and schedule song to start at t0"""
        self.stop()
        self._song = song
        self._t0 = t0
        self._reset_playback_state()
        self._done.clear()

        if not self.enabled:
            print(f"[music] {song.name} loaded, not playing it (no --audio-device given)")
            return

        import sounddevice as sd

        device = self._device if self._device is not None else self._default_output()
        info = sd.query_devices(device, "output")
        hostapi = sd.query_hostapis(info["hostapi"])["name"]
        extra = sd.WasapiSettings(auto_convert=True) if "WASAPI" in hostapi else None

        self._stream = sd.OutputStream(
            samplerate=song.samplerate,
            channels=song.channels,
            dtype="int16",
            device=device,
            latency="low",
            extra_settings=extra,
            callback=self._callback,
            finished_callback=self._done.set,
        )
        self._stream.start()
        print(f"[music] {song.name} starts in {t0 - time.time():.2f}s on {info['name']} ({hostapi}), "
              f"output latency {self._stream.latency * 1000:.1f}ms")

    @staticmethod
    def _default_output() -> Optional[int]:
        """The system default output, preferring WASAPI's on Windows since MME's latency reporting is poor"""
        import sounddevice as sd
        if sys.platform == "win32":
            for api in sd.query_hostapis():
                if "WASAPI" in api["name"] and api["default_output_device"] >= 0:
                    return api["default_output_device"]
        return None

    def stop(self):
        """Fade out and close the stream, if one is open"""
        stream = self._stream
        if stream is None:
            return
        # measure before fading out, the callbacks while stopping aren't evenly timed
        self._log_drift()
        if self._pos is not None and not self._finished and stream.active:
            self._fade_remaining = max(1, int(self.FADE_S * self._song.samplerate))
            self._fading = True
            self._done.wait(0.25)
        stream.close(ignore_errors=True)
        self._stream = None

    def _callback(self, outdata: np.ndarray, frames: int, time_info, status):
        import sounddevice as sd

        if status.output_underflow:
            self._underflows += 1
        song = self._song
        assert song is not None
        rate_hz = song.samplerate

        now = time.time()
        if time_info.outputBufferDacTime > 0 and time_info.currentTime > 0:
            # time.time() is read a little after PortAudio stamps currentTime, and later
            # still when the callback is held up, so the smallest offset seen is the true one.
            # Rise slowly to follow the controller's clock being slewed by NTP.
            offset = now - time_info.currentTime
            if self._wall_offset is None or offset < self._wall_offset:
                self._wall_offset = offset
            else:
                self._wall_offset += self.WALL_OFFSET_RISE * (offset - self._wall_offset)
            dac_wall = time_info.outputBufferDacTime + self._wall_offset
        else:
            # some ALSA/Pulse setups don't report timestamps
            dac_wall = now + self._stream.latency

        # the song sample that should be reaching the DAC at the start of this buffer
        ideal = (dac_wall - (self._t0 + self.offset_s)) * rate_hz

        if self._pos is None:
            if ideal + frames <= 0 or self._fading:
                outdata.fill(0)
                if self._fading:
                    raise sd.CallbackStop
                return
            lead = max(0, int(round(-ideal)))
            self._pos = max(0.0, float(round(ideal)))
            self._ref_wall = self._last_dac_wall = dac_wall
            outdata[:lead] = 0
            self._render(outdata[lead:], 1.0)
        elif self._fading:
            self._render(outdata, 1.0)
        else:
            self._last_dac_wall = dac_wall
            error = (self._pos - ideal) / rate_hz  # seconds the audio is ahead of the lights
            self._error += self.ERROR_SMOOTHING * (error - self._error)

            rate = 1.0
            if abs(self._error) > self.RESYNC_THRESHOLD_S:
                self._pos = max(0.0, float(round(ideal)))
                self._error = 0.0
                self._correcting = False
                self._resyncs += 1
                self._ref_wall, self._ref_error, self._corrected = dac_wall, 0.0, 0.0
            elif self._correcting or abs(self._error) > self.DRIFT_THRESHOLD_S:
                self._correcting = abs(self._error) > self.DRIFT_SETTLED_S
                if self._correcting:
                    rate = 1 - self.SLEW_RATE if self._error > 0 else 1 + self.SLEW_RATE
            self._render(outdata, rate)

        if self._fading:
            self._apply_fade(outdata)
            if self._fade_remaining <= 0:
                raise sd.CallbackStop
        elif self._pos >= len(song.samples):
            self._finished = True
            self._log_drift()
            raise sd.CallbackStop

    def _render(self, out: np.ndarray, rate: float):
        """Fill out from the song at the current position, reading rate song samples per output sample"""
        samples = self._song.samples
        n = len(out)
        if rate == 1.0:
            i = int(round(self._pos))
            chunk = samples[i:i + n]
            out[:len(chunk)] = chunk
            out[len(chunk):] = 0
            self._pos = float(i + n)
        else:
            self._corrected += n * (rate - 1)
            idx = self._pos + np.arange(n) * rate
            valid = idx < len(samples) - 1
            i0 = idx[valid].astype(np.int64)
            frac = (idx[valid] - i0)[:, None]
            out[:] = 0
            out[valid] = (samples[i0] * (1 - frac) + samples[i0 + 1] * frac).astype(np.int16)
            self._pos += n * rate

    def _apply_fade(self, out: np.ndarray):
        total = max(1, int(self.FADE_S * self._song.samplerate))
        n = len(out)
        gain = np.clip((self._fade_remaining - np.arange(n)) / total, 0.0, 1.0)
        out[:] = (out * gain[:, None]).astype(np.int16)
        self._fade_remaining -= n

    def drift_ppm(self) -> Optional[float]:
        """How fast the sound card's clock runs against the controller's, in parts per million"""
        if self._song is None:
            return None
        elapsed = self._last_dac_wall - self._ref_wall
        if elapsed < 5:
            return None
        uncorrected = self._error - self._ref_error - self._corrected / self._song.samplerate
        return uncorrected / elapsed * 1e6

    def _log_drift(self):
        if self._drift_logged or self._pos is None or self._song is None:
            return
        self._drift_logged = True
        ppm = self.drift_ppm()
        measured = f"{ppm:+.1f}ppm" if ppm is not None else "too short to measure"
        print(f"[music] {self._song.name}: sound card drift {measured}, "
              f"{self._resyncs} resync(s), {self._underflows} underflow(s)")

    def status(self) -> dict:
        """A snapshot of the player, for GET /audio"""
        song = self._song
        playing = self._stream is not None and self._pos is not None and not self._finished
        ppm = self.drift_ppm()
        return {
            "enabled": self.enabled,
            "device": self._device,
            "offset_ms": self.offset_s * 1000,
            "song": song.name if song is not None else None,
            "duration_s": song.duration if song is not None else None,
            "playing": playing,
            "position_s": self._pos / song.samplerate if song is not None and self._pos is not None else None,
            "error_ms": self._error * 1000,
            "drift_ppm": ppm,
            "resyncs": self._resyncs,
            "underflows": self._underflows,
        }


player = AudioPlayer()
