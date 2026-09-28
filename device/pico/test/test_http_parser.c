#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "core/http_parser.h"

static http_parse_result_t feed_all(http_parser_t *p, const char *data, size_t *consumed_out) {
    size_t consumed = 0;
    http_parse_result_t r = http_parser_feed(p, (const uint8_t *)data, strlen(data), &consumed);
    if (consumed_out) *consumed_out = consumed;
    return r;
}

int main(void) {
    http_parser_t p;

    /* GET /status, no headers of interest */
    http_parser_reset(&p);
    assert(feed_all(&p, "GET /status HTTP/1.1\r\nHost: pico\r\n\r\n", NULL) == HTTP_PARSE_HEADERS_DONE);
    const http_request_t *req = http_parser_request(&p);
    assert(req->method == HTTP_METHOD_GET);
    assert(strcmp(req->path, "/status") == 0);
    assert(!req->have_content_length);

    /* POST /frame with both custom headers + Content-Length, body bytes fed
     * in the same call and correctly left unconsumed for the caller */
    http_parser_reset(&p);
    const char *req_str =
        "POST /frame HTTP/1.1\r\n"
        "Content-Type: application/octet-stream\r\n"
        "X-Frame-Seq: 42\r\n"
        "X-Frame-Time: 1732000000.125\r\n"
        "Content-Length: 9\r\n"
        "\r\n"
        "BODYBYTES";
    size_t total_len = strlen(req_str);
    size_t consumed;
    assert(http_parser_feed(&p, (const uint8_t *)req_str, total_len, &consumed) == HTTP_PARSE_HEADERS_DONE);
    req = http_parser_request(&p);
    assert(req->method == HTTP_METHOD_POST);
    assert(strcmp(req->path, "/frame") == 0);
    assert(req->have_content_length && req->content_length == 9);
    assert(req->have_frame_seq && req->frame_seq == 42);
    assert(req->have_frame_time);
    assert(req->frame_time_s > 1732000000.124 && req->frame_time_s < 1732000000.126);
    assert(total_len - consumed == 9);
    assert(memcmp(req_str + consumed, "BODYBYTES", 9) == 0);

    /* fed one byte at a time - must behave identically to one big feed() */
    http_parser_reset(&p);
    const char *req2 = "POST /clear HTTP/1.1\r\n\r\n";
    http_parse_result_t last = HTTP_PARSE_NEED_MORE;
    for (size_t i = 0; i < strlen(req2); i++) {
        size_t c;
        last = http_parser_feed(&p, (const uint8_t *)&req2[i], 1, &c);
        if (last != HTTP_PARSE_NEED_MORE) break;
    }
    assert(last == HTTP_PARSE_HEADERS_DONE);
    req = http_parser_request(&p);
    assert(req->method == HTTP_METHOD_POST);
    assert(strcmp(req->path, "/clear") == 0);

    /* WebSocket upgrade on the same listener - recognised by its key, with
     * any bytes after the headers (the first WS frame) left unconsumed */
    http_parser_reset(&p);
    const char *upgrade =
        "GET / HTTP/1.1\r\n"
        "Host: pico:8420\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
        "\x82\x85";
    assert(feed_all(&p, upgrade, &consumed) == HTTP_PARSE_HEADERS_DONE);
    req = http_parser_request(&p);
    assert(req->method == HTTP_METHOD_GET);
    assert(req->have_ws_key && strcmp(req->ws_key, "dGhlIHNhbXBsZSBub25jZQ==") == 0);
    assert(strlen(upgrade) - consumed == 2);

    /* a plain GET /status carries no key, so it isn't mistaken for one */
    http_parser_reset(&p);
    assert(feed_all(&p, "GET /status HTTP/1.1\r\n\r\n", NULL) == HTTP_PARSE_HEADERS_DONE);
    assert(!http_parser_request(&p)->have_ws_key);

    /* unknown method -> error */
    http_parser_reset(&p);
    assert(feed_all(&p, "PUT /frame HTTP/1.1\r\n\r\n", NULL) == HTTP_PARSE_ERROR);

    printf("http_parser: all tests passed\n");
    return 0;
}
