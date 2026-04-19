import logging
from typing import Tuple
from transport import BaseTransport, register

log = logging.getLogger(__name__)

_ENCODE_TABLE = bytes(b ^ 0xFF for b in range(256))

@register
class InvertTransport(BaseTransport):

    name = "invert"

    def encode(self, data: bytes) -> bytes:
        return data.translate(_ENCODE_TABLE)

    def decode(self, buf: bytes) -> Tuple[bytes, bytes]:
        return buf.translate(_ENCODE_TABLE), b''