# PT

## File layout

```txt
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
| --- | --- |
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

```sh
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
TOR_PT_MANAGED_TRANSPORT_VER=1        \
TOR_PT_STATE_LOCATION=/tmp/pt_state   \
TOR_PT_CLIENT_TRANSPORTS=foobar       \
PT_LOG_LEVEL=DEBUG                    \
python3 main.py
```

```bash
export TOR_PT_MANAGED_TRANSPORT_VER=1
export TOR_PT_STATE_LOCATION=/tmp/pt-state
export TOR_PT_CLIENT_TRANSPORTS=obfs4
export TOR_PT_EXIT_ON_STDIN_CLOSE=1
```

Expected stdout:

```bash
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
from transports.mytransport import MyTransport
```

That's it — the transport is automatically available.  
Use it in torrc with `ServerTransportPlugin mytransport exec …`.
