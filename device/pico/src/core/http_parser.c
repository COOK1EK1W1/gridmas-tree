#include "core/http_parser.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

void http_parser_reset(http_parser_t *p) {
    memset(p, 0, sizeof(*p));
    p->state = HTTP_STATE_REQUEST_LINE;
}

static bool starts_with_ci(const char *s, const char *prefix) {
    while (*prefix) {
        if (tolower((unsigned char)*s) != tolower((unsigned char)*prefix)) return false;
        s++;
        prefix++;
    }
    return true;
}

static const char *skip_ws(const char *s) {
    while (*s == ' ' || *s == '\t') s++;
    return s;
}

static void parse_request_line(http_parser_t *p) {
    const char *s = p->line;
    if (starts_with_ci(s, "GET ")) {
        p->request.method = HTTP_METHOD_GET;
        s += 4;
    } else if (starts_with_ci(s, "POST ")) {
        p->request.method = HTTP_METHOD_POST;
        s += 5;
    } else {
        p->state = HTTP_STATE_ERROR;
        return;
    }

    s = skip_ws(s);
    size_t i = 0;
    while (*s && *s != ' ' && i + 1 < sizeof(p->request.path)) {
        p->request.path[i++] = *s++;
    }
    p->request.path[i] = '\0';
    if (*s != ' ') {
        p->state = HTTP_STATE_ERROR; /* path too long, or no HTTP-version token followed it */
        return;
    }
    /* the rest of the line (HTTP version) is deliberately ignored */
}

static void parse_header_line(http_parser_t *p) {
    if (p->line_len == 0) {
        p->state = HTTP_STATE_DONE; /* blank line ends the header block */
        return;
    }

    char *colon = strchr(p->line, ':');
    if (!colon) return; /* malformed header line - ignore it rather than fail the whole request */
    *colon = '\0';
    const char *name = p->line;
    const char *value = skip_ws(colon + 1);

    if (starts_with_ci(name, "Content-Length")) {
        p->request.content_length = (uint32_t)strtoul(value, NULL, 10);
        p->request.have_content_length = true;
    } else if (starts_with_ci(name, "X-Frame-Seq")) {
        p->request.frame_seq = (uint32_t)strtoul(value, NULL, 10);
        p->request.have_frame_seq = true;
    } else if (starts_with_ci(name, "X-Frame-Time")) {
        p->request.frame_time_s = strtod(value, NULL);
        p->request.have_frame_time = true;
    }
    /* any other header is accepted and silently ignored */
}

http_parse_result_t http_parser_feed(http_parser_t *p, const uint8_t *data, size_t len, size_t *consumed) {
    size_t i = 0;
    for (; i < len; i++) {
        char c = (char)data[i];

        if (c == '\r') continue; /* strip CR, act on LF */

        if (c != '\n') {
            if (p->line_len + 1 < sizeof(p->line)) {
                p->line[p->line_len++] = c;
            }
            /* an over-long line is silently truncated rather than erroring -
             * the fields we actually read (path, header values) are short */
            continue;
        }

        p->line[p->line_len] = '\0';

        if (p->state == HTTP_STATE_REQUEST_LINE) {
            parse_request_line(p);
            if (p->state != HTTP_STATE_ERROR) p->state = HTTP_STATE_HEADERS;
        } else if (p->state == HTTP_STATE_HEADERS) {
            parse_header_line(p);
        }

        p->line_len = 0;

        if (p->state == HTTP_STATE_DONE || p->state == HTTP_STATE_ERROR) {
            i++;
            break;
        }
    }

    *consumed = i;

    if (p->state == HTTP_STATE_DONE) return HTTP_PARSE_HEADERS_DONE;
    if (p->state == HTTP_STATE_ERROR) return HTTP_PARSE_ERROR;
    return HTTP_PARSE_NEED_MORE;
}

const http_request_t *http_parser_request(const http_parser_t *p) {
    return &p->request;
}
