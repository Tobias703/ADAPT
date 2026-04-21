# Example Transport 'foobar':
#   Encoding:
#     Each input bit is expanded to 3 output bytes (1:24 expansion).
#     For every bit of the input byte, MSB-first:
#       bit == 1 -> b'foo' (3 bytes)
#       bit == 0 -> b'bar' (3 bytes)

#   Example 0xAB = 10101011:
#     1->foo  0->bar  1->foo  0->bar  1->foo  0->bar  1->foo  1->foo
#     wire: b'foobarfoobarfoobarfoofoo' (24 bytes)

#   Decoding:
#     Consume the buffer in 24-byte chunks.  Each chunk maps back to one byte.
#     Any trailing bytes that don't form a complete 24-byte chunk are buffered as the remainder for the next call.

import logging
from typing import Tuple

from helpers.transport import BaseTransport, register

log = logging.getLogger(__name__)


def _build_encode_table():
    # Return a 256-entry list where entry[i] is the 24-byte encoding of byte i
    table = []
    for byte_val in range(256):
        encoded = b""
        # MSB first
        for bit_pos in range(7, -1, -1):
            if (byte_val >> bit_pos) & 1:
                encoded += b"foo"
            else:
                encoded += b"bar"
        table.append(encoded)
    return table


_ENCODE_TABLE = _build_encode_table()

# Reverse lookup: 3-byte token -> bit value
# Unknown tokens are treated as 0 via dict.get(token, 0) - never raise.
_TOKEN_TO_BIT = {b"foo": 1, b"bar": 0}

_FRAME_BITS = 8
_FRAME_BYTES = 3
_FRAME_SIZE = _FRAME_BITS * _FRAME_BYTES


@register
class FoobarTransport(BaseTransport):
    # Stateless Transport - the same instance can be reused across calls, but the relay engine creates a fresh instance per connection anyway.

    name = "foobar"

    def encode(self, data: bytes) -> bytes:
        # O(n) encoding via pre-computed lookup table.
        # Output length == len(data) * 24.
        if not data:
            return b""
        return b"".join(_ENCODE_TABLE[b] for b in data)

    def decode(self, buf: bytes) -> Tuple[bytes, bytes]:
        # Decode as many complete 24-byte frames as possible from buf.

        # Returns (decoded_bytes, remaining_buf).
        # remaining_buf will be prepended to the next incoming chunk by the relay.

        # Corrupted tokens (neither b'foo' nor b'bar') are treated as 0-bits and a warning is logged. We never raise from decode() because an unhandled exception in _pump_decode would silently close the relay connection before the ORPort has a chance to respond, causing the bridge to return empty packets back to the client.
        if not buf:
            return b"", b""

        n_frames = len(buf) // _FRAME_SIZE
        if n_frames == 0:
            return b"", buf

        output = bytearray(n_frames)
        for frame_idx in range(n_frames):
            base = frame_idx * _FRAME_SIZE
            byte_val = 0
            for bit_idx in range(8):
                token = buf[base + bit_idx * _FRAME_BYTES : base + bit_idx * _FRAME_BYTES + _FRAME_BYTES]
                bit = _TOKEN_TO_BIT.get(token)
                if bit is None:
                    log.warning(
                        "foobar: unknown token %r at frame %d bit %d - treating as 0",
                        token,
                        frame_idx,
                        bit_idx,
                    )
                    bit = 0
                byte_val = (byte_val << 1) | bit
            output[frame_idx] = byte_val

        consumed = n_frames * _FRAME_SIZE
        return bytes(output), buf[consumed:]
