#include "core/ws_handshake.h"

#include <stdint.h>
#include <string.h>

/* SHA-1 (RFC 3174) - not exposed beyond this file; the only thing this
 * module needs it for is the WS handshake's accept-key hash. */

typedef struct {
    uint32_t state[5];
    uint64_t bit_count;
    uint8_t  buffer[64];
    size_t   buffer_len;
} sha1_ctx_t;

static uint32_t rol32(uint32_t v, int bits) {
    return (v << bits) | (v >> (32 - bits));
}

static void sha1_process_block(sha1_ctx_t *ctx, const uint8_t block[64]) {
    uint32_t w[80];
    for (int i = 0; i < 16; i++) {
        w[i] = ((uint32_t)block[i * 4] << 24) | ((uint32_t)block[i * 4 + 1] << 16) |
               ((uint32_t)block[i * 4 + 2] << 8) | (uint32_t)block[i * 4 + 3];
    }
    for (int i = 16; i < 80; i++) w[i] = rol32(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);

    uint32_t a = ctx->state[0], b = ctx->state[1], c = ctx->state[2], d = ctx->state[3], e = ctx->state[4];

    for (int i = 0; i < 80; i++) {
        uint32_t f, k;
        if (i < 20) { f = (b & c) | ((~b) & d); k = 0x5A827999u; }
        else if (i < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1u; }
        else if (i < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDCu; }
        else { f = b ^ c ^ d; k = 0xCA62C1D6u; }

        uint32_t temp = rol32(a, 5) + f + e + k + w[i];
        e = d; d = c; c = rol32(b, 30); b = a; a = temp;
    }

    ctx->state[0] += a; ctx->state[1] += b; ctx->state[2] += c; ctx->state[3] += d; ctx->state[4] += e;
}

static void sha1_init(sha1_ctx_t *ctx) {
    ctx->state[0] = 0x67452301u; ctx->state[1] = 0xEFCDAB89u; ctx->state[2] = 0x98BADCFEu;
    ctx->state[3] = 0x10325476u; ctx->state[4] = 0xC3D2E1F0u;
    ctx->bit_count = 0;
    ctx->buffer_len = 0;
}

static void sha1_update(sha1_ctx_t *ctx, const uint8_t *data, size_t len) {
    ctx->bit_count += (uint64_t)len * 8;
    while (len > 0) {
        size_t n = 64 - ctx->buffer_len;
        if (n > len) n = len;
        memcpy(ctx->buffer + ctx->buffer_len, data, n);
        ctx->buffer_len += n;
        data += n;
        len -= n;
        if (ctx->buffer_len == 64) {
            sha1_process_block(ctx, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
}

static void sha1_final(sha1_ctx_t *ctx, uint8_t out[20]) {
    uint64_t bit_count = ctx->bit_count; /* snapshot before the padding below inflates it */
    uint8_t pad = 0x80;
    sha1_update(ctx, &pad, 1);
    uint8_t zero = 0;
    while (ctx->buffer_len != 56) sha1_update(ctx, &zero, 1);
    uint8_t len_bytes[8];
    for (int i = 0; i < 8; i++) len_bytes[i] = (uint8_t)(bit_count >> (56 - 8 * i));
    sha1_update(ctx, len_bytes, 8);

    for (int i = 0; i < 5; i++) {
        out[i * 4] = (uint8_t)(ctx->state[i] >> 24);
        out[i * 4 + 1] = (uint8_t)(ctx->state[i] >> 16);
        out[i * 4 + 2] = (uint8_t)(ctx->state[i] >> 8);
        out[i * 4 + 3] = (uint8_t)ctx->state[i];
    }
}

static void base64_encode(const uint8_t *data, size_t len, char *out) {
    static const char table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t i = 0, o = 0;
    while (i + 3 <= len) {
        uint32_t n = ((uint32_t)data[i] << 16) | ((uint32_t)data[i + 1] << 8) | data[i + 2];
        out[o++] = table[(n >> 18) & 0x3F];
        out[o++] = table[(n >> 12) & 0x3F];
        out[o++] = table[(n >> 6) & 0x3F];
        out[o++] = table[n & 0x3F];
        i += 3;
    }
    size_t rem = len - i;
    if (rem == 1) {
        uint32_t n = (uint32_t)data[i] << 16;
        out[o++] = table[(n >> 18) & 0x3F];
        out[o++] = table[(n >> 12) & 0x3F];
        out[o++] = '=';
        out[o++] = '=';
    } else if (rem == 2) {
        uint32_t n = ((uint32_t)data[i] << 16) | ((uint32_t)data[i + 1] << 8);
        out[o++] = table[(n >> 18) & 0x3F];
        out[o++] = table[(n >> 12) & 0x3F];
        out[o++] = table[(n >> 6) & 0x3F];
        out[o++] = '=';
    }
    out[o] = '\0';
}

void ws_compute_accept_key(const char *client_key, char accept_out[29]) {
    static const char guid[] = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
    char combined[64];
    size_t key_len = strlen(client_key);
    size_t guid_len = strlen(guid);
    if (key_len > sizeof(combined) - guid_len - 1) key_len = sizeof(combined) - guid_len - 1; /* a real Sec-WebSocket-Key is always 24 bytes */
    memcpy(combined, client_key, key_len);
    memcpy(combined + key_len, guid, guid_len);

    sha1_ctx_t ctx;
    sha1_init(&ctx);
    sha1_update(&ctx, (const uint8_t *)combined, key_len + guid_len);
    uint8_t digest[20];
    sha1_final(&ctx, digest);

    base64_encode(digest, sizeof(digest), accept_out);
}
