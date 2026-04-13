# pt-python-dispatcher

A **PT Spec 3.0**-compliant Pluggable Transport dispatcher written in pure Python (stdlib only).  
Ships with the **`foobar`** demo transport and a clean factory for adding your own.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLIENT SIDE                                                │
│                                                             │
│  Tor ──SOCKS5──► PT Client (socks5.py + pt_client.py)      │
│                       │ TCP  encode(data) ──────────────────┼──► PT Server
└───────────────────────┼─────────────────────────────────────┘    │
                        │                                           │ decode
┌───────────────────────┼─────────────────────────────────────┐    ▼
│  SERVER SIDE          │                                     │  ORPort
│                       │ TCP  encoded(data)                  │
│  PT Server (pt_server.py) ──decode──► ORPort (Tor)          │
│  PT Server (pt_server.py) ◄──encode── ORPort (Tor)          │
└─────────────────────────────────────────────────────────────┘
```

IPC with the parent process (Tor) happens entirely over **stdout** using newline-terminated ASCII lines.

---

## File layout

```
pt_foobar/
├── main.py          Entry point, signal handling, stdin EOF watch
├── config.py        PT 3.0 CLI flags + PT 1.0 env var parser, version negotiation
├── ipc.py           All stdout IPC messages (VERSION, CMETHOD, SMETHOD, LOG, …)
├── socks5.py        Async RFC 1928 SOCKS5 server; auth methods 0x00 and 0x09
├── relay.py         Bidirectional async relay with encode/decode pump tasks
├── transport.py     BaseTransport ABC + @register decorator + factory
├── pt_client.py     Client-mode dispatcher (SOCKS5 → encode → TCP)
├── pt_server.py     Server-mode dispatcher (TCP → decode → ORPort)
├── transports/
│   ├── __init__.py  Imports all bundled transports (triggers @register)
│   └── foobar.py   Demo: bit 1 → "foo", bit 0 → "bar"  (1:24 expansion)
├── pt_foobar.spec   PyInstaller build spec
└── build.sh         One-step binary build script
```

---

## PT Spec compliance

| Feature | Status |
|---|---|
| Version negotiation (`-ptversion` / `TOR_PT_MANAGED_TRANSPORT_VER`) | ✅ |
| PT 3.0 CLI flags | ✅ |
| PT 1.0/2.0 env var fallback | ✅ |
| `VERSION` / `VERSION-ERROR` | ✅ |
| `ENV-ERROR` | ✅ |
| `PROXY DONE` / `PROXY-ERROR` | ✅ (error if upstream proxy set) |
| `CMETHOD … socks5` / `CMETHOD-ERROR` / `CMETHODS DONE` | ✅ |
| `SMETHOD` / `SMETHOD-ERROR` / `SMETHODS DONE` | ✅ |
| Unknown transports silently skipped (no CMETHOD-ERROR) | ✅ |
| `LOG SEVERITY=… MESSAGE=…` | ✅ |
| `STATUS TYPE=version …` | ✅ |
| SOCKS5 auth method 0x00 (no auth) | ✅ |
| SOCKS5 auth method 0x09 (JSON Parameter Block, IANA PT) | ✅ |
| stdin EOF → clean shutdown | ✅ |
| SIGTERM → clean shutdown | ✅ |
| PyInstaller single-binary (Shadow compatible) | ✅ |

---

## Torrc configuration

### Bridge (server side)

```
# torrc for the bridge relay
ServerTransportPlugin foobar exec /path/to/dist/pt_foobar
ServerTransportListenAddr foobar 0.0.0.0:4911
ExtORPort auto
```

### Client side

```
# torrc for the Tor client
UseBridges 1
Bridge foobar <bridge_ip>:4911
ClientTransportPlugin foobar exec /path/to/dist/pt_foobar
```

---

## Running directly (for testing / Shadow)

### Server mode — environment variables (PT 1.0 / Tor style)

```bash
TOR_PT_STATE_LOCATION=/tmp/pt_state          \
TOR_PT_MANAGED_TRANSPORT_VER=1               \
TOR_PT_SERVER_TRANSPORTS=foobar              \
TOR_PT_SERVER_BINDADDR=foobar-0.0.0.0:4911  \
TOR_PT_ORPORT=127.0.0.1:9001                 \
PT_LOG_LEVEL=DEBUG                           \
python3 main.py
```

Expected stdout:
```
VERSION 1
STATUS TYPE=version IMPLEMENTATION=pt-python-dispatcher VERSION=1.0.0
SMETHOD foobar 0.0.0.0:4911
SMETHODS DONE
```

### Server mode — CLI flags (PT 3.0)

```bash
python3 main.py                     \
  -ptversion 3.0                    \
  -state /tmp/pt_state              \
  -mode server                      \
  -transports foobar                \
  -bindaddr foobar-0.0.0.0:4911    \
  -orport 127.0.0.1:9001
```

### Client mode — environment variables (PT 1.0 / Tor style)

```bash
TOR_PT_STATE_LOCATION=/tmp/pt_state   \
TOR_PT_MANAGED_TRANSPORT_VER=1        \
TOR_PT_CLIENT_TRANSPORTS=foobar       \
PT_LOG_LEVEL=DEBUG                    \
python3 main.py
```

Expected stdout:
```
VERSION 1
STATUS TYPE=version IMPLEMENTATION=pt-python-dispatcher VERSION=1.0.0
CMETHOD foobar socks5 127.0.0.1:<port>
CMETHODS DONE
```

---

## Shadow configuration

Shadow needs the binary path and the PT environment variables.  Example `shadow.yaml` snippet:

```yaml
hosts:
  pt-bridge:
    processes:
      - path: /path/to/dist/pt_foobar
        environment:
          TOR_PT_MANAGED_TRANSPORT_VER: "1"
          TOR_PT_STATE_LOCATION: "/tmp/pt_state"
          TOR_PT_SERVER_TRANSPORTS: "foobar"
          TOR_PT_SERVER_BINDADDR: "foobar-0.0.0.0:4911"
          TOR_PT_ORPORT: "127.0.0.1:9001"
        start_time: 1
```

Build the binary first with `./build.sh` (requires PyInstaller).

---

## Adding a custom transport

Create `transports/mytransport.py`:

```python
from transport import BaseTransport, register

@register
class MyTransport(BaseTransport):
    """XOR every byte with a fixed key — simple demo."""

    name = "mytransport"          # ← wire name used in torrc / IPC
    KEY  = 0x42

    def encode(self, data: bytes) -> bytes:
        return bytes(b ^ self.KEY for b in data)

    def decode(self, buf: bytes) -> tuple:
        # XOR is self-inverse; no framing so always complete output
        return bytes(b ^ self.KEY for b in buf), b''
```

Then add one import line to `transports/__init__.py`:

```python
from transports.mytransport import MyTransport  # noqa: F401
```

That's it — the transport is automatically available.  
Use it in torrc with `ServerTransportPlugin mytransport exec …`.

---

## The foobar transport in Wireshark

Capture traffic on the PT server port (default 4911) and apply the filter  
`tcp.port == 4911`. Every payload will be pure printable ASCII:

```
666f6f626172666f6f626172...
f o o b a r f o o b a r ...
```

Each group of 24 bytes represents one original plaintext byte.  
It is immediately obvious this is not normal TLS — which is the point for a demo.

---

## Dependencies

**None.** Only Python 3.11+ standard library is used.  
The `build.sh` script adds `pyinstaller` as a build-time dependency only.
