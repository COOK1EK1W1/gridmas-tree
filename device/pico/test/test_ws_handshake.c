#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "core/ws_handshake.h"

int main(void) {
    /* RFC 6455 section 1.3's own worked example */
    char accept[29];
    ws_compute_accept_key("dGhlIHNhbXBsZSBub25jZQ==", accept);
    assert(strcmp(accept, "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=") == 0);

    printf("ws_handshake: all tests passed\n");
    return 0;
}
