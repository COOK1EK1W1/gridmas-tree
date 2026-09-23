#ifndef CORE_HTTP_PARSER_H
#define CORE_HTTP_PARSER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Minimal incremental HTTP/1.1 request-line + header parser, used by
 * hw/http_server.c for the two endpoints it serves (GET /status,
 * POST /clear) and by hw/ws_frame_server.c to parse the WebSocket upgrade
 * request's Sec-WebSocket-Key (see docs/docs/network-pixel-protocol.md).
 * Deliberately not general-purpose:
 * fixed small buffers, no chunked encoding, no multi-value headers.
 *
 * The content_length/frame_seq/frame_time_s fields below date from when
 * POST /frame's body followed these same headers on this same TCP
 * connection; http_server.c no longer reads a body at all (both remaining
 * routes are bodyless), but the fields are left in place rather than
 * churning this shared, host-tested module (see test/test_http_parser.c)
 * for routes it no longer needs to special-case.
 *
 * No Pico SDK dependency - built and unit-tested on a host machine (see
 * test/test_http_parser.c).
 */

#define HTTP_MAX_PATH_LEN 32
#define HTTP_MAX_LINE_LEN 128

typedef enum {
    HTTP_METHOD_UNKNOWN,
    HTTP_METHOD_GET,
    HTTP_METHOD_POST,
} http_method_t;

typedef struct {
    http_method_t method;
    char path[HTTP_MAX_PATH_LEN];

    bool     have_content_length;
    uint32_t content_length;

    bool     have_frame_seq;
    uint32_t frame_seq;

    bool     have_frame_time;
    double   frame_time_s; /* unix epoch seconds, as sent in X-Frame-Time */

    bool     have_ws_key;
    char     ws_key[32]; /* Sec-WebSocket-Key, base64 - always 24 chars in practice */
} http_request_t;

typedef enum {
    HTTP_PARSE_NEED_MORE,    /* keep calling feed() with more bytes */
    HTTP_PARSE_HEADERS_DONE, /* request line + headers parsed; see http_parser_request() */
    HTTP_PARSE_ERROR,        /* malformed request; caller should respond 400 and close */
} http_parse_result_t;

typedef struct {
    enum { HTTP_STATE_REQUEST_LINE, HTTP_STATE_HEADERS, HTTP_STATE_DONE, HTTP_STATE_ERROR } state;
    char   line[HTTP_MAX_LINE_LEN];
    size_t line_len;
    http_request_t request;
} http_parser_t;

void http_parser_reset(http_parser_t *p);

/* Feed bytes as they arrive from the socket. Consumes as many bytes as it
 * needs from `data` (up to `len`) and reports how many via *consumed - a
 * caller with bytes left over beyond what the parser consumed (i.e. the
 * start of the request body, once HTTP_PARSE_HEADERS_DONE is returned)
 * should treat the remainder as body bytes itself. */
http_parse_result_t http_parser_feed(http_parser_t *p, const uint8_t *data, size_t len, size_t *consumed);

const http_request_t *http_parser_request(const http_parser_t *p);

#endif
