# Tor / parent-process startup sequence:
#   1. Parent sets env vars (PT 1.0/2.x) or passes CLI flags (PT 3.0)
#   2. Parent execs this process
#   3. This process:
#     a. Negotiates protocol version        ->  VERSION <ver>
#     b. Validates config                   ->  ENV-ERROR (and exit) if bad
#     c. Emits STATUS TYPE=version          ->  (informational)
#     d. Initialises transport listeners
#     e. Emits CMETHOD/SMETHOD lines        ->  one per transport
#     f. Emits CMETHODS/SMETHODS DONE       ->  parent now routes traffic
#     g. Waits for SIGTERM / EOF on stdin
#   4. Parent sends SIGTERM to shut down

import asyncio
import logging
import os
import signal
import sys
import io
from typing import cast

from helpers.config import parse_config, IMPLEMENTATION_NAME, IMPLEMENTATION_VERSION
from helpers.pt_client import run_client
from helpers.pt_bridge import run_bridge
import helpers.ipc as ipc

# Register all bundled transports so that their @register decorators fire
import transports  # noqa: F401

# Force unbuffered binary stdout
if hasattr(sys.stdout, "reconfigure"):
    stdout = cast(io.TextIOWrapper, sys.stdout)
    try:
        stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

# Logging goes to stderr (stdout is reserved for PT IPC)
_log_level_name = os.environ.get("PT_LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, _log_level_name, logging.WARNING),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ppt_dispatcher")


async def _async_main() -> None:
    # Parse config + version negotiation (may sys.exit on error)
    cfg = parse_config()

    # Announce our software version (informational; parent will most likely ignore)
    ipc.emit_status_version(IMPLEMENTATION_NAME, IMPLEMENTATION_VERSION)

    log.info(
        "PPT dispatcher starting  mode=%s  transports=%s  protocol=%s",
        cfg.mode,
        cfg.transports,
        cfg.protocol_version,
    )

    # Start transport listeners
    if cfg.mode == "client":
        await run_client(cfg)
    else:
        await run_bridge(cfg)

    # Wait for shutdown signal
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_signal(sig_num: int) -> None:
        log.info("Received signal %d - shutting down", sig_num)
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
    log.info("PPT dispatcher exiting cleanly")


async def _watch_stdin(stop: asyncio.Event) -> None:
    # Tor closes the dispatcher's stdin when it wants the PT to exit.
    # Watch for EOF and set the stop event.
    loop = asyncio.get_running_loop()
    try:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                log.info("stdin EOF - shutting down")
                stop.set()
                return
    except Exception as exc:
        log.debug("stdin watcher exiting: %s", exc)


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
