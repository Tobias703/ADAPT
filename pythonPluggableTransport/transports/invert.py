# Example Transport 'invert':
#   Encoding:
#     Each input bit is inverted (XORed with 0xFF)

#   Example 0xAB = 0b10101011:
#     1->0  0->1  1->0  0->1  1->0  0->1  1->0  1->0
#     wire: 0x54 = 0b01010100 (1 byte)

#   Decoding:
#     Each input bit is inverted (XORed with 0xFF)

import logging
from typing import Tuple
from helpers.transport import BaseTransport, register

log = logging.getLogger(__name__)

_ENCODE_TABLE = bytes(b ^ 0xFF for b in range(256))


@register
class InvertTransport(BaseTransport):
    name = "invert"

    def encode(self, data: bytes) -> bytes:
        return data.translate(_ENCODE_TABLE)

    def decode(self, buf: bytes) -> Tuple[bytes, bytes]:
        return buf.translate(_ENCODE_TABLE), b""
