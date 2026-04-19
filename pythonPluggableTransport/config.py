# PT configuration parser

# Supports both:
#   - PT 3.0 command-line flags  (-ptversion, -state, -transports, …)
#   - PT 1.0/2.0 environment variables  (TOR_PT_MANAGED_TRANSPORT_VER, …)

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import ipc

# Versions this implementation supports, in preference order.
# Tor sends "1" (not "1.0") for PT spec v1; PT 3.0 sends "3.0".
# We accept both forms for maximum compatibility.
SUPPORTED_VERSIONS = ["3.0", "2.1", "2.0", "1.0", "1"]

IMPLEMENTATION_NAME = "python-pluggable-transport"
IMPLEMENTATION_VERSION = "1.0.0"


@dataclass
class PTConfig:
    # 'client' | 'server'
    mode: str
    # negotiated PT spec version string
    protocol_version: str
    # writable state directory
    state_dir: str
    # (names of) requested transports
    transports: List[str]

    # Client-only
    upstream_proxy: Optional[str] = None  # e.g. "socks5://127.0.0.1:9050"

    # Server-only
    # "host:port" of ORPort
    or_port: Optional[str] = None
    # "host:port" of ExtORPort (optional)
    ext_or_port: Optional[str] = None
    # name -> "host:port"
    bind_addrs: Dict[str, str] = field(default_factory=dict)
    # name -> "key=value;…"
    server_options: Dict[str, str] = field(default_factory=dict)
    # Per-transport options (from -options / -optionsFile / TOR_PT_SERVER_TRANSPORT_OPTIONS)
    transport_options: Dict[str, dict] = field(default_factory=dict)


def _negotiate_version(versions_str: str) -> Optional[str]:
    # PT versions are sent via a comma-separated supported-versions string.
    # This function returns either the best mutually supported version or 'None'.
    parent = {v.strip() for v in versions_str.split(",") if v.strip()}
    for v in SUPPORTED_VERSIONS:
        if v in parent:
            return v
    return None


def _parse_bindaddr(raw: str) -> Dict[str, str]:
    # Parse TOR_PT_SERVER_BINDADDR / -bindaddr value.
    # Format: "transport1-host:port,transport2-host:port,…"
    # The transport name ends at the first '-'.
    result: Dict[str, str] = {}
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        dash = token.find("-")
        if dash == -1:
            continue
        name = token[:dash]
        addr = token[dash + 1 :]
        result[name] = addr
    return result


def _parse_server_transport_options(raw: str) -> Dict[str, str]:
    # Parse TOR_PT_SERVER_TRANSPORT_OPTIONS.
    # Format: "transportName1:key1=value2,key2=value2;transportName2:key1=value1;…"
    # Colons, semicolons, and backslashes are backslash-escaped.
    # Returns {transportName: "key=value string"}.
    # Example: TOR_PT_SERVER_TRANSPORT_OPTIONS=obfs4:cert=XYZ;iat-mode=0;snowflake:stun=stun.example.com
    result: Dict[str, str] = {}
    i = 0
    current = []
    segments = []
    while i < len(raw):
        c = raw[i]
        if c == "\\" and i + 1 < len(raw):
            current.append(raw[i + 1])
            i += 2
        elif c == ";":
            segments.append("".join(current))
            current = []
            i += 1
        else:
            current.append(c)
            i += 1
    if current:
        segments.append("".join(current))
    for seg in segments:
        colon = seg.find(":")
        if colon == -1:
            continue
        result[seg[:colon]] = seg[colon + 1 :]
    return result


def parse_config() -> PTConfig:
    # Parse PT configuration and perform version negotiation.
    # Writes VERSION / VERSION-ERROR / ENV-ERROR to stdout and may sys.exit(1).

    # 1. Parse CLI flags (PT 3.0)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-ptversion", default=None)
    parser.add_argument("-state", default=None)
    parser.add_argument("-transports", default=None)
    parser.add_argument("-proxy", default=None)
    parser.add_argument("-bindaddr", default=None)
    parser.add_argument("-orport", default=None)
    parser.add_argument("-extorport", default=None)
    parser.add_argument("-options", default=None)
    parser.add_argument("-optionsFile", default=None)
    parser.add_argument(
        "-mode",
        default=None,
        choices=[
            "client",
            "server",
            "transparent-TCP",
            "STUN-aware-UDP",
            "transparent-UDP",
        ],
    )
    args, _ = parser.parse_known_args()

    # 2. Version negotiation
    # PT 3.0: -ptversion flag; PT 1.0/2.0: TOR_PT_MANAGED_TRANSPORT_VER env var
    versions_raw = args.ptversion or os.environ.get("TOR_PT_MANAGED_TRANSPORT_VER")

    if versions_raw:
        ver = _negotiate_version(versions_raw)
        if ver is None:
            ipc.emit_version_error("no-version")
            sys.exit(1)
        ipc.emit_version(ver)
        protocol_version = ver
    else:
        # No version hint from parent - assume PT 1.0 (Tor compatibility)
        ipc.emit_version("1.0")
        protocol_version = "1.0"

    # 3. State directory
    state_dir = args.state or os.environ.get("TOR_PT_STATE_LOCATION", "/tmp/pt_state")
    os.makedirs(state_dir, exist_ok=True)

    # 4. Determine mode
    mode = args.mode
    if not mode:
        if os.environ.get("TOR_PT_CLIENT_TRANSPORTS"):
            mode = "client"
        elif os.environ.get("TOR_PT_SERVER_TRANSPORTS"):
            mode = "server"
        else:
            ipc.emit_env_error(
                "Cannot determine mode: set -mode or TOR_PT_CLIENT/SERVER_TRANSPORTS"
            )
            sys.exit(1)
    if mode not in ("client", "server"):
        ipc.emit_env_error(f"Mode '{mode}' is not supported by this implementation")
        sys.exit(1)

    # 5. Transports
    if args.transports:
        transports = [t.strip() for t in args.transports.split(",") if t.strip()]
    elif mode == "client" and os.environ.get("TOR_PT_CLIENT_TRANSPORTS"):
        transports = [
            t.strip()
            for t in os.environ["TOR_PT_CLIENT_TRANSPORTS"].split(",")
            if t.strip()
        ]
    elif mode == "server" and os.environ.get("TOR_PT_SERVER_TRANSPORTS"):
        transports = [
            t.strip()
            for t in os.environ["TOR_PT_SERVER_TRANSPORTS"].split(",")
            if t.strip()
        ]
    else:
        ipc.emit_env_error("No transports specified")
        sys.exit(1)

    # 6. Build config object
    cfg = PTConfig(
        mode=mode,
        protocol_version=protocol_version,
        state_dir=state_dir,
        transports=transports,
    )

    # 7. Client extras
    if mode == "client":
        cfg.upstream_proxy = args.proxy or os.environ.get("TOR_PT_PROXY")

    # 8. Server extras
    if mode == "server":
        or_port = args.orport or os.environ.get("TOR_PT_ORPORT")
        if not or_port:
            ipc.emit_env_error("Server mode requires -orport / TOR_PT_ORPORT")
            sys.exit(1)
        cfg.or_port = or_port

        cfg.ext_or_port = args.extorport or os.environ.get(
            "TOR_PT_EXTENDED_SERVER_PORT"
        )

        bind_raw = args.bindaddr or os.environ.get("TOR_PT_SERVER_BINDADDR", "")
        if bind_raw:
            cfg.bind_addrs = _parse_bindaddr(bind_raw)

        opts_raw = os.environ.get("TOR_PT_SERVER_TRANSPORT_OPTIONS", "")
        if opts_raw:
            cfg.server_options = _parse_server_transport_options(opts_raw)

    return cfg
