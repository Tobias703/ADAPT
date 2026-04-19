
"""
transports/foobar.py — The "foobar" demo transport

Encoding:
  Each input byte is expanded to 24 output bytes.
  For every bit of the input byte, MSB-first:
    bit == 1  →  b'foo'   (3 bytes)
    bit == 0  →  b'bar'   (3 bytes)

  One input byte (8 bits) × 3 bytes/bit = 24 output bytes.
  Traffic expansion ratio: 1:24.

Example (byte 0xAB = 0b10101011):
  1→foo  0→bar  1→foo  0→bar  1→foo  0→bar  1→foo  1→foo
  wire: b'foobarfoobarfoobarfoofoo'  (24 bytes)

This looks delightfully obvious in Wireshark — every payload is pure
printable ASCII spelling "foobar" in various combinations.

Decoding:
  Consume the buffer in 24-byte chunks.  Each chunk maps back to one byte.
  Any trailing bytes that don't form a complete 24-byte chunk are returned
  as the remainder for the next call.
"""

from transport import BaseTransport, register


# ──────────────────────────────────────────────────────────────────────────────
# Pre-computed encode table  (built once at import time)
# ──────────────────────────────────────────────────────────────────────────────

def _build_encode_table():
    """Return a 256-entry list where entry[i] is the 24-byte encoding of byte i."""
    table = []
    for byte_val in range(256):
        encoded = b''
        for bit_pos in range(7, -1, -1):          # MSB first
            if (byte_val >> bit_pos) & 1:
                encoded += b'foo'
            else:
                encoded += b'bar'
        table.append(encoded)
    return table


_ENCODE_TABLE = _build_encode_table()

# Reverse lookup: 3-byte token → bit value
_TOKEN_TO_BIT = {b'foo': 1, b'bar': 0}

# Bytes per encoded byte on the wire
_FRAME_SIZE = 24   # 8 bits × 3 bytes


# ──────────────────────────────────────────────────────────────────────────────
# Transport class
# ──────────────────────────────────────────────────────────────────────────────

@register
class FoobarTransport(BaseTransport):
    """
    Demo transport: replaces every binary 1 with 'foo' and every binary 0
    with 'bar', operating at the individual bit level.

    Stateless — the same instance can be reused across calls, but the relay
    engine creates a fresh instance per connection anyway.
    """

    name = "foobar"

    # ── encode ────────────────────────────────────────────────────────────────

    def encode(self, data: bytes) -> bytes:
        """
        O(n) encoding via pre-computed lookup table.
        Output length == len(data) * 24.
        """
        if not data:
            return b''
        return b''.join(_ENCODE_TABLE[b] for b in data)

    # ── decode ────────────────────────────────────────────────────────────────

    def decode(self, buf: bytes) -> tuple:   # (bytes, bytes)
        """
        Decode as many complete 24-byte frames as possible from buf.

        Returns (decoded_bytes, remaining_buf).
        remaining_buf will be prepended to the next incoming chunk by the relay.

        Corrupted tokens (neither b'foo' nor b'bar') are treated as 0-bits and
        do not raise — this keeps the relay alive for debugging purposes.
        """
        if not buf:
            return b'', b''

        n_frames = len(buf) // _FRAME_SIZE
        if n_frames == 0:
            return b'', buf

        output = bytearray(n_frames)
        for frame_idx in range(n_frames):
            base = frame_idx * _FRAME_SIZE
            byte_val = 0
            for bit_idx in range(8):
                token = buf[base + bit_idx * 3: base + bit_idx * 3 + 3]
                byte_val = (byte_val << 1) | _TOKEN_TO_BIT.get(token, 0)
            output[frame_idx] = byte_val

        consumed = n_frames * _FRAME_SIZE
        return bytes(output), buf[consumed:]
