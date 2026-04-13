"""
main.py — PT dispatcher entry point

Tor / parent-process startup sequence
──────────────────────────────────────
  1. Parent sets env vars (PT 1.0) or passes CLI flags (PT 3.0)
  2. Parent exec()s this process
  3. This process:
       a. Negotiates protocol version        →  VERSION <ver>
       b. Validates config                   →  ENV-ERROR (and exit) if bad
       c. Emits STATUS TYPE=version          →  (informational)
       d. Initialises transport listeners
       e. Emits CMETHOD/SMETHOD lines        →  one per transport
       f. Emits CMETHODS/SMETHODS DONE       →  parent now routes traffic
       g. Waits for SIGTERM / EOF on stdin
  4. Parent sends SIGTERM to shut down

Shadow compatibility notes
───────────────────────────
  Shadow simulates the network and filesystem but runs real ELF binaries.
  Build with PyInstaller (see build.sh) to produce a single-file binary.
  Shadow intercepts epoll/select so asyncio works transparently.
  stdout must be unbuffered — we write via sys.stdout.buffer directly.
  Signal handling uses asyncio's add_signal_handler() which calls into the
  event loop, safe under Shadow's simulated clock.
"""

import asyncio
import logging
import os
import signal
import sys
import io
from typing import cast

# ── Force unbuffered binary stdout ────────────────────────────────────────────
# The PT IPC protocol requires each line to arrive atomically and promptly.
# We always write via sys.stdout.buffer in ipc.py, but set the underlying fd
# to O_NONBLOCK-safe line-buffering as a belt-and-suspenders measure.
if hasattr(sys.stdout, 'reconfigure'):
    stdout = cast(io.TextIOWrapper, sys.stdout)
    try:
        stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

# ── Logging goes to stderr (stdout is reserved for PT IPC) ───────────────────
_log_level_name = os.environ.get('PT_LOG_LEVEL', 'WARNING').upper()
logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, _log_level_name, logging.WARNING),
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('pt_dispatcher')

# ── Register all bundled transports (side effect: @register decorators fire) ──
import transports  # noqa: F401, E402

from config import parse_config, IMPLEMENTATION_NAME, IMPLEMENTATION_VERSION
from pt_client import run_client
from pt_server import run_server
import ipc


# ──────────────────────────────────────────────────────────────────────────────
# Async main
# ──────────────────────────────────────────────────────────────────────────────

async def _async_main() -> None:
    # ── Parse config + version negotiation (may sys.exit on error) ────────────
    cfg = parse_config()

    # ── Announce our software version (informational; parent may ignore) ──────
    ipc.emit_status_version(IMPLEMENTATION_NAME, IMPLEMENTATION_VERSION)

    log.info("PT dispatcher starting  mode=%s  transports=%s  protocol=%s",
             cfg.mode, cfg.transports, cfg.protocol_version)

    # ── Start transport listeners ─────────────────────────────────────────────
    if cfg.mode == 'client':
        await run_client(cfg)
    else:
        await run_server(cfg)

    # ── Wait for shutdown signal ──────────────────────────────────────────────
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_signal(sig_num: int) -> None:
        log.info("Received signal %d — shutting down", sig_num)
        ipc.emit_log("notice", f"Received signal {sig_num}, shutting down")
        stop.set()

    # Register for both SIGTERM (from Tor) and SIGINT (Ctrl-C in dev)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _on_signal, sig)
        except (NotImplementedError, RuntimeError):
            # Windows / environments that don't support add_signal_handler
            pass

    # Also exit if Tor closes stdin (standard PT shutdown mechanism)
    asyncio.create_task(_watch_stdin(stop))

    await stop.wait()
    log.info("PT dispatcher exiting cleanly")


async def _watch_stdin(stop: asyncio.Event) -> None:
    """
    Tor closes the dispatcher's stdin when it wants the PT to exit.
    Watch for EOF and set the stop event.
    """
    loop = asyncio.get_running_loop()
    try:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                log.info("stdin EOF — shutting down")
                stop.set()
                return
    except Exception as exc:
        log.debug("stdin watcher exiting: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    asyncio.run(_async_main())


if __name__ == '__main__':
    main()
