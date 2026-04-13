# transports/foobar.py

"""
foobar transport (demo / test transport)

Encoding:
    Each bit of input expands to 3 bytes:
        1 -> b"foo"
        0 -> b"bar"

    So 1 byte (8 bits) → 24 bytes output.

Decoding:
    Reads input in chunks of 3 bytes and reconstructs bits.
    Incomplete trailing data is buffered via the decode contract.
"""

from typing import Tuple
from transport import BaseTransport, register


@register
class FoobarTransport(BaseTransport):
    name = "foobar"

    # Precomputed lookup tables (critical for performance)
    _ENCODE_TABLE = {
        0: b"bar",
        1: b"foo",
    }

    _DECODE_TABLE = {
        b"bar": 0,
        b"foo": 1,
    }

    def encode(self, data: bytes) -> bytes:
        if not data:
            return b""

        out = bytearray()

        for byte in data:
            # Process bits MSB → LSB (network order)
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                out += self._ENCODE_TABLE[bit]

        return bytes(out)

    def decode(self, buf: bytes) -> Tuple[bytes, bytes]:
        if not buf:
            return b"", b""
    
        out = bytearray()
    
        chunk_size = 3
        total_len = len(buf)
    
        # Number of complete 3-byte symbols
        n_symbols = total_len // chunk_size
    
        # Only full symbols usable
        usable_len = n_symbols * chunk_size
    
        # We need groups of 8 symbols to form 1 byte
        n_full_bytes = n_symbols // 8
    
        # Number of symbols actually consumed
        symbols_used = n_full_bytes * 8
    
        idx = 0
    
        for _ in range(n_full_bytes):
            byte = 0
            for _ in range(8):
                chunk = buf[idx:idx + 3]
                idx += 3
    
                try:
                    bit = self._DECODE_TABLE[chunk]
                except KeyError:
                    raise ValueError(f"Invalid foobar chunk: {chunk!r}")
    
                byte = (byte << 1) | bit
    
            out.append(byte)
    
        # Remaining bytes:
        remaining = buf[symbols_used * chunk_size:]
    
        return bytes(out), remaining