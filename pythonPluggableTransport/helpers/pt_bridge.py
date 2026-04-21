# As per spec:
#   - Bind address comes from -bindaddr flag or # TOR_PT_SERVER_BINDADDR env var. If not specified for a transport, bind to 0.0.0.0:0 # (OS-assigned port).
#   - OR port comes from -orport / TOR_PT_ORPORT.
#   - SMETHODS DONE is sent after all transports are initialised.
# Note:
#   - Extended OR port (ExtORPort) support is detected but this implementation falls back to plain ORPort for simplicity.

import asyncio
import logging

import helpers.ipc as ipc
import helpers.relay as relay_mod
import helpers.transport as transport_mod
from helpers.config import PTConfig

log = logging.getLogger(__name__)


def _split_addr(addr: str) -> tuple:
    # Split "host:port" or "[ipv6]:port" into (host_str, port_int).
    if addr.startswith("["):
        bracket_end = addr.index("]")
        host = addr[1:bracket_end]
        port = int(addr[bracket_end + 2 :])
    else:
        last_colon = addr.rfind(":")
        host = addr[:last_colon]
        port = int(addr[last_colon + 1 :])
    return host, port


async def _handle_connection(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    transport_name: str,
    or_host: str,
    or_port: int,
) -> None:
    # Handle one inbound encoded connection from a PT client.

    # Steps:
    #   1. Open TCP connection to ORPort
    #   2. Bidirectional relay: decode client->ORPort, encode ORPort->client

    peer = client_writer.get_extra_info("peername", ("?", 0))
    log.debug("[%s] PT server connection, transport=%s", peer, transport_name)

    # Connect to ORPort
    try:
        or_reader, or_writer = await asyncio.open_connection(or_host, or_port)
    except OSError as exc:
        log.warning(
            "[%s] Cannot connect to ORPort %s:%d - %s", peer, or_host, or_port, exc
        )
        try:
            client_writer.close()
        except Exception:
            pass
        return

    # Create transport instance
    transport = transport_mod.create(transport_name)

    # Relay with inverse transform vs client mode (client = encoded side, ORPort = plain side; a to b = client -> ORPort; b to a = ORPort -> client)
    await relay_mod.relay(
        client_reader,
        client_writer,
        or_reader,
        or_writer,
        a_to_b_fn=transport.decode,
        a_to_b_is_decode=True,
        b_to_a_fn=transport.encode,
        b_to_a_is_decode=False,
    )
    log.debug("[%s] relay finished", peer)


async def run_bridge(cfg: PTConfig) -> None:
    # Start one listener per requested transport and emit SMETHOD lines.

    # Parse OR port
    try:
        or_host, or_port = _split_addr(cfg.or_port)
    except (ValueError, IndexError) as exc:
        ipc.emit_env_error(f"Invalid OR port address {cfg.or_port!r}: {exc}")
        return

    if cfg.ext_or_port:
        log.info(
            "ExtORPort configured (%s) - using plain ORPort instead (ExtORPort framing not implemented)",
            cfg.ext_or_port,
        )

    for name in cfg.transports:
        # Silently skip unknown transports as per spec
        if not transport_mod.is_registered(name):
            log.info("Skipping unknown transport: %r", name)
            continue

        if name in cfg.bind_addrs:
            raw = cfg.bind_addrs[name]
            try:
                bind_host, bind_port = _split_addr(raw)
            except (ValueError, IndexError) as exc:
                ipc.emit_smethod_error(name, f"bad bind address {raw!r}: {exc}")
                continue
        else:
            bind_host = "0.0.0.0"
            bind_port = 0

        try:
            server = await asyncio.start_server(
                lambda r, w, n=name, h=or_host, p=or_port: _handle_connection(
                    r, w, n, h, p
                ),
                host=bind_host,
                port=bind_port,
            )
        except OSError as exc:
            ipc.emit_smethod_error(name, str(exc))
            log.error("Failed to start server listener for %r: %s", name, exc)
            continue

        bound = server.sockets[0].getsockname()
        listen_addr = f"{bound[0]}:{bound[1]}"
        ipc.emit_smethod(name, listen_addr)
        log.info(
            "Transport %r server listener ready at %s  (ORPort -> %s:%d)",
            name,
            listen_addr,
            or_host,
            or_port,
        )

        asyncio.get_running_loop().create_task(server.serve_forever())

    ipc.emit_smethods_done()
