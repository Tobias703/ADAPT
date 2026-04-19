# Supported authentication methods:
#   0x00  NO AUTHENTICATION REQUIRED (RFC 1928)
#   0x09  JSON Parameter Block       (IANA-assigned for Pluggable Transports)

# The JSON Parameter Block (method 0x09) lets the SOCKS5 client pass per-connection PT arguments (e.g. bridge fingerprint, options) inline in the SOCKS handshake.  It was specifically assigned by IANA for the PT spec.

# Sub-negotiation for method 0x09:
#   Client -> Server:  uint16-BE(len)  json-utf8(len bytes)
#   Server -> Client:  0x01 0x00   (version=1, status=success)

# Only CONNECT command is supported (no BIND or UDP ASSOCIATE).

import asyncio
import json
import logging
import struct
from typing import Optional, Tuple

log = logging.getLogger(__name__)

SOCKS5_VER = 0x05

# Auth methods
METHOD_NO_AUTH = 0x00
METHOD_JSON_PARAMS = 0x09  # IANA assignment for PT spec
METHOD_NO_ACCEPTABLE = 0xFF

# Commands
CMD_CONNECT = 0x01

# Address types
ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03
ATYP_IPV6 = 0x04

# Reply codes
REP_SUCCESS = 0x00
REP_GENERAL_FAILURE = 0x01
REP_NET_UNREACHABLE = 0x03
REP_HOST_UNREACHABLE = 0x04
REP_CONN_REFUSED = 0x05
REP_CMD_NOT_SUPPORTED = 0x07
REP_ATYP_NOT_SUPPORTED = 0x08


def _build_reply(rep: int, bind_host: str = "0.0.0.0", bind_port: int = 0) -> bytes:
    import socket

    try:
        addr_bytes = socket.inet_aton(bind_host)
        atyp = ATYP_IPV4
    except OSError:
        addr_bytes = b"\x00\x00\x00\x00"
        atyp = ATYP_IPV4
    return (
        bytes([SOCKS5_VER, rep, 0x00, atyp]) + addr_bytes + struct.pack(">H", bind_port)
    )


async def do_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> Optional[Tuple[str, int, dict]]:
    # Perform the full SOCKS5 handshake (method negotiation + optional auth + CONNECT request).

    # Returns (host, port, pt_args) on success, or 'None' on any error.
    # 'pt_args' is a dict of per-connection PT arguments (may be empty).

    # The caller is responsible for sending the final success/failure reply via 'send_reply()' once the outbound connection is established.
    try:
        return await _handshake_inner(reader, writer)
    except (
        asyncio.IncompleteReadError,
        ConnectionResetError,
        BrokenPipeError,
        OSError,
    ) as exc:
        log.debug("SOCKS5 handshake error: %s", exc)
        return None


async def _handshake_inner(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> Optional[Tuple[str, int, dict]]:
    # Inner (may raise) version of do_handshake

    # Phase 1: Method negotiation
    hdr = await reader.readexactly(2)
    ver, nmethods = hdr[0], hdr[1]

    if ver != SOCKS5_VER:
        log.debug("SOCKS5: wrong version byte 0x%02x", ver)
        writer.close()
        return None

    methods = set(await reader.readexactly(nmethods))

    # Prefer JSON param block if offered; otherwise no-auth
    if METHOD_JSON_PARAMS in methods:
        chosen = METHOD_JSON_PARAMS
    elif METHOD_NO_AUTH in methods:
        chosen = METHOD_NO_AUTH
    else:
        writer.write(bytes([SOCKS5_VER, METHOD_NO_ACCEPTABLE]))
        await writer.drain()
        writer.close()
        return None

    writer.write(bytes([SOCKS5_VER, chosen]))
    await writer.drain()

    # Phase 1.5: JSON parameter block sub-negotiation
    pt_args: dict = {}
    if chosen == METHOD_JSON_PARAMS:
        len_bytes = await reader.readexactly(2)
        json_len = struct.unpack(">H", len_bytes)[0]
        if json_len > 0:
            json_raw = await reader.readexactly(json_len)
            try:
                pt_args = json.loads(json_raw.decode("utf-8"))
                if not isinstance(pt_args, dict):
                    pt_args = {}
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                log.debug("SOCKS5: bad JSON param block: %s", exc)
                pt_args = {}
        # Sub-negotiation reply: version=0x01, status=0x00 (success)
        writer.write(bytes([0x01, 0x00]))
        await writer.drain()

    # Phase 2: CONNECT request
    req = await reader.readexactly(4)
    ver, cmd, _rsv, atyp = req[0], req[1], req[2], req[3]

    if ver != SOCKS5_VER:
        await _send_reply(writer, REP_GENERAL_FAILURE)
        writer.close()
        return None

    if cmd != CMD_CONNECT:
        await _send_reply(writer, REP_CMD_NOT_SUPPORTED)
        writer.close()
        return None

    # Parse destination address
    if atyp == ATYP_IPV4:
        host_bytes = await reader.readexactly(4)
        host = ".".join(str(b) for b in host_bytes)

    elif atyp == ATYP_DOMAIN:
        domain_len = (await reader.readexactly(1))[0]
        host = (await reader.readexactly(domain_len)).decode("ascii", errors="replace")

    elif atyp == ATYP_IPV6:
        import socket as _socket

        host_bytes = await reader.readexactly(16)
        host = _socket.inet_ntop(_socket.AF_INET6, host_bytes)

    else:
        await _send_reply(writer, REP_ATYP_NOT_SUPPORTED)
        writer.close()
        return None

    port_bytes = await reader.readexactly(2)
    port = struct.unpack(">H", port_bytes)[0]

    log.debug("SOCKS5: CONNECT %s:%d  pt_args=%s", host, port, pt_args)
    return host, port, pt_args


async def _send_reply(writer: asyncio.StreamWriter, rep: int) -> None:
    writer.write(_build_reply(rep))
    await writer.drain()


async def send_success(
    writer: asyncio.StreamWriter, bind_host: str = "127.0.0.1", bind_port: int = 0
) -> None:
    # Send SOCKS5 success reply (REP=0x00) with optional bound address
    writer.write(_build_reply(REP_SUCCESS, bind_host, bind_port))
    await writer.drain()


async def send_failure(
    writer: asyncio.StreamWriter, rep: int = REP_GENERAL_FAILURE
) -> None:
    # Send SOCKS5 failure reply
    await _send_reply(writer, rep)
