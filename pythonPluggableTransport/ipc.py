"""
ipc.py — Pluggable Transport IPC protocol (PT spec 3.0 / Tor PT spec 1.0)

All communication to the parent process goes through newline-terminated lines
written to stdout.  Stderr is for human-readable logging only.

Grammar (from spec):
  <Line>       ::= <Keyword> <OptArgs> <NL>
  <Keyword>    ::= <KeywordChar>+
  <KeywordChar> ::= US-ASCII alphanumeric | '-' | '_'
  <OptArgs>    ::= (<SP> <ArgChar>+)*
  <ArgChar>    ::= any US-ASCII except NUL and NL
"""

import sys
import threading

_lock = threading.Lock()

# ──────────────────────────────────────────────────────────────────────────────
# Internal helper
# ──────────────────────────────────────────────────────────────────────────────

def _emit(line: str) -> None:
    """Write one IPC line to stdout, thread-safely, with immediate flush."""
    with _lock:
        # Write as bytes so we bypass any text-mode buffering subtleties
        sys.stdout.buffer.write((line + '\n').encode('ascii'))
        sys.stdout.buffer.flush()


# ──────────────────────────────────────────────────────────────────────────────
# Common messages (§1.2.1 in PT 3.0 / §3.3.1 in PT 1.0)
# ──────────────────────────────────────────────────────────────────────────────

def emit_version(ver: str) -> None:
    """Announce the PT spec version we will use. Must be emitted first."""
    _emit(f"VERSION {ver}")


def emit_version_error(msg: str = "no-version") -> None:
    """No compatible version found. Process MUST exit after this."""
    _emit(f"VERSION-ERROR {msg}")


def emit_env_error(msg: str) -> None:
    """Configuration environment variables could not be parsed. Must exit."""
    _emit(f"ENV-ERROR {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# Client messages
# ──────────────────────────────────────────────────────────────────────────────

def emit_proxy_done() -> None:
    """Upstream proxy (TOR_PT_PROXY) validated and will be used."""
    _emit("PROXY DONE")


def emit_proxy_error(msg: str) -> None:
    """Upstream proxy is malformed or unsupported. Process MUST exit."""
    _emit(f"PROXY-ERROR {msg}")


def emit_cmethod(transport: str, addr: str) -> None:
    """A client-side transport listener is ready. addr = 'host:port'."""
    _emit(f"CMETHOD {transport} socks5 {addr}")


def emit_cmethod_error(transport: str, msg: str) -> None:
    """A client-side transport could not be started."""
    _emit(f"CMETHOD-ERROR {transport} {msg}")


def emit_cmethods_done() -> None:
    """All client-side transports have been initialised (or skipped)."""
    _emit("CMETHODS DONE")


# ──────────────────────────────────────────────────────────────────────────────
# Server messages
# ──────────────────────────────────────────────────────────────────────────────

def emit_smethod(transport: str, addr: str, args: dict | None = None) -> None:
    """
    A server-side transport listener is ready.
    addr  = 'host:port' that PT clients should connect to.
    args  = optional per-transport key/value pairs forwarded in Bridge line.
    """
    line = f"SMETHOD {transport} {addr}"
    if args:
        def _escape(s: str) -> str:
            return s.replace('\\', '\\\\').replace('=', '\\=').replace(',', '\\,')
        args_str = ','.join(f"{_escape(k)}={_escape(v)}" for k, v in args.items())
        line += f" ARGS:{args_str}"
    _emit(line)


def emit_smethod_error(transport: str, msg: str) -> None:
    """A server-side transport could not be started."""
    _emit(f"SMETHOD-ERROR {transport} {msg}")


def emit_smethods_done() -> None:
    """All server-side transports have been initialised (or skipped)."""
    _emit("SMETHODS DONE")


# ──────────────────────────────────────────────────────────────────────────────
# Log and status messages (PT 1.0 extensions, widely supported)
# ──────────────────────────────────────────────────────────────────────────────

def emit_log(severity: str, message: str) -> None:
    """
    Send a human-readable log message to the parent process.
    severity ∈ {error, warning, notice, info, debug}
    """
    # CString-quote the message if it contains whitespace or quotes
    if any(c in message for c in (' ', '\t', '"')):
        message = '"' + message.replace('\\', '\\\\').replace('"', '\\"') + '"'
    _emit(f"LOG SEVERITY={severity} MESSAGE={message}")


def emit_status_version(implementation: str, version: str) -> None:
    """Report software name and version to parent (informational)."""
    _emit(f"STATUS TYPE=version IMPLEMENTATION={implementation} VERSION={version}")
