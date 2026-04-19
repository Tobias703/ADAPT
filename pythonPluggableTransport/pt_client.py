# Per the spec:
#   - Unknown transports are silently skipped (MUST NOT produce CMETHOD-ERROR)
#   - Listeners bind to 127.0.0.1 on an OS-assigned port
#   - CMETHOD lines use the 'socks5' keyword
#   - CMETHODS DONE is sent after all transports are initialised

import asyncio
import logging


import ipc
import socks5
import relay as relay_mod
import transport as transport_mod
from config import PTConfig

log = logging.getLogger(__name__)


async def _handle_connection(client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter, transport_name: str) -> None:
    # Handle one inbound SOCKS5 connection from Tor.
    # Steps:
    #   1. Complete SOCKS5 handshake (supports method 0x00 and 0x09)
    #   2. Open TCP connection to the PT server (host:port from SOCKS5 CONNECT)
    #   3. Send SOCKS5 success reply to Tor
    #   4. Bidirectional relay: encode Tor->server, decode server->Tor
    
    peer = client_writer.get_extra_info('peername', ('?', 0))
    log.debug("[%s] client connection -> transport=%s", peer, transport_name)

    # SOCKS5 handshake
    result = await socks5.do_handshake(client_reader, client_writer)
    if result is None:
        log.debug("[%s] SOCKS5 handshake failed", peer)
        return
    host, port, pt_args = result
    log.debug("[%s] SOCKS5 CONNECT %s:%d", peer, host, port)

    # Connect to PT server
    try:
        srv_reader, srv_writer = await asyncio.open_connection(host, port)
    except OSError as exc:
        log.warning("[%s] Cannot connect to PT server %s:%d - %s", peer, host, port, exc)
        await socks5.send_failure(client_writer, socks5.REP_CONN_REFUSED)
        return

    # SOCKS5 success
    await socks5.send_success(client_writer)

    # Create transport instance (per-connection; may hold session state)
    transport = transport_mod.create(transport_name)

    # Relay with transform
    await relay_mod.relay(client_reader, client_writer, srv_reader, srv_writer, a_to_b_fn=transport.encode, a_to_b_is_decode=False, b_to_a_fn=transport.decode, b_to_a_is_decode=True,)
    log.debug("[%s] relay finished", peer)


async def run_client(cfg: PTConfig) -> None:
    # Start one SOCKS5 listener per requested transport and emit CMETHOD lines.
    # After all transports are (attempted to be) started, emit CMETHODS DONE.
    
    # Upstream proxy
    if cfg.upstream_proxy:
        log.warning("Upstream proxy configured (%s) but not supported; aborting", cfg.upstream_proxy)
        ipc.emit_proxy_error("upstream proxy chaining not supported by this implementation")
        return

    for name in cfg.transports:
        if not transport_mod.is_registered(name):
            # Spec 3.3.2.2: unknown transports MUST be silently skipped
            log.info("Skipping unknown transport: %r", name)
            continue

        try:
            # port=0 -> let OS pick a free port
            server = await asyncio.start_server(lambda r, w, n=name: _handle_connection(r, w, n), host='127.0.0.1', port=0)                
        except OSError as exc:
            ipc.emit_cmethod_error(name, str(exc))
            log.error("Failed to start SOCKS5 listener for %r: %s", name, exc)
            continue

        bound = server.sockets[0].getsockname()
        listen_addr = f"{bound[0]}:{bound[1]}"
        ipc.emit_cmethod(name, listen_addr)
        log.info("Transport %r client listener ready at %s", name, listen_addr)

        asyncio.get_running_loop().create_task(server.serve_forever())

    ipc.emit_cmethods_done()
