"""
test_pt.py — Pluggable Transport test suite

Run with:  python3 -m unittest -v test_pt

Test matrix
───────────
  Unit — FoobarTransport
    encode / decode roundtrip (single byte, multi-byte, all 256 values)
    partial-frame buffering in decode
    empty-input contract  encode(b'') == b''  decode(b'') == (b'', b'')
    output size invariant  len(encode(n bytes)) == n * 24
    decode discards incomplete trailing tokens

  IPC stdout (PT spec compliance)
    server mode: VERSION  SMETHOD <name>  SMETHODS DONE emitted in order
    client mode: VERSION  CMETHOD <name> socks5 <addr>  CMETHODS DONE in order
    no error lines (ENV-ERROR / VERSION-ERROR / CMETHOD-ERROR / SMETHOD-ERROR)
    unknown transport silently skipped — no *-ERROR line, DONE still emitted
    missing ORPort in server mode → ENV-ERROR and non-zero exit

  Lifecycle
    SIGTERM → clean exit (code 0 or -SIGTERM)
    stdin EOF → clean exit

  End-to-end data flow  (requires both PT processes + mock ORPort)
    client → server direction: data sent via SOCKS5 arrives plain at mock ORPort
    server → client direction: data from mock ORPort arrives plain at SOCKS5 client
    bidirectional simultaneous transfer
    multiple sequential connections over the same SOCKS5 listener
"""

import os
import queue
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate the PT source directory (same directory as this test file)
# ---------------------------------------------------------------------------
PT_DIR = Path(__file__).parent.resolve()


# ===========================================================================
# Helpers
# ===========================================================================

def _free_port() -> int:
    """Return an unused TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# PTProcess — subprocess wrapper with line-oriented stdout reader
# ---------------------------------------------------------------------------

class PTProcess:
    """
    Wraps a PT dispatcher subprocess.

    Spawns a reader thread that queues stdout lines.  Provides
    ``wait_for_line(prefix)`` which blocks until a line starting with
    *prefix* appears, with a configurable timeout.
    """

    def __init__(self, args: list, env: dict, *, timeout: float = 10.0):
        self._timeout = timeout
        full_env = {**os.environ, **env}
        self.proc = subprocess.Popen(
            [sys.executable] + args,
            cwd=str(PT_DIR),
            env=full_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        self._lines: list[str] = []
        self._q: queue.Queue[str] = queue.Queue()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self) -> None:
        assert self.proc.stdout is not None
        for raw in self.proc.stdout:
            line = raw.decode('ascii', errors='replace').rstrip('\n\r')
            self._lines.append(line)
            self._q.put(line)

    # ── public API ─────────────────────────────────────────────────────────

    def wait_for_line(self, prefix: str, timeout: float | None = None) -> str:
        """
        Return the first stdout line that starts with *prefix*.

        Checks already-collected lines first (so order of calls doesn't matter),
        then blocks on the queue.  Raises ``TimeoutError`` if *timeout* elapses.
        """
        if timeout is None:
            timeout = self._timeout
        # Check buffered lines first
        for line in self._lines:
            if line.startswith(prefix):
                return line
        # Wait for new lines
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            try:
                line = self._q.get(timeout=min(remaining, 0.2))
                if line.startswith(prefix):
                    return line
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
        raise TimeoutError(
            f"Timed out waiting for stdout line starting with {prefix!r}.\n"
            f"Lines so far: {self._lines}"
        )

    def all_stdout(self) -> list[str]:
        """Return a snapshot of all stdout lines collected so far."""
        return list(self._lines)

    def terminate(self, wait: float = 5.0) -> int:
        """Send SIGTERM and wait for the process to exit.  Returns exit code."""
        try:
            self.proc.send_signal(signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            code = self.proc.wait(timeout=wait)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            code = self.proc.wait()
        # Close all pipe file objects so Python doesn't warn about leaked fds
        for fh in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if fh is not None:
                try:
                    fh.close()
                except OSError:
                    pass
        return code

    def close_stdin(self) -> None:
        """Close the subprocess stdin to trigger the stdin-EOF shutdown path."""
        if self.proc.stdin and not self.proc.stdin.closed:
            self.proc.stdin.close()

    def wait(self, timeout: float = 5.0) -> int:
        try:
            code = self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            code = self.proc.wait()
        for fh in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if fh is not None:
                try:
                    fh.close()
                except OSError:
                    pass
        return code

    def stderr_text(self) -> str:
        """Read all stderr (blocks until process exits)."""
        assert self.proc.stderr is not None
        return self.proc.stderr.read().decode('utf-8', errors='replace')

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.proc.poll() is None:
            self.terminate()
        # Close all pipe file objects so Python doesn't warn about leaked fds
        for fh in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if fh is not None:
                try:
                    fh.close()
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# PTLauncher — convenience factory
# ---------------------------------------------------------------------------

def _state_dir() -> str:
    return tempfile.mkdtemp(prefix='pt_state_')


def launch_server(transport: str, or_addr: str,
                  bind_addr: str | None = None) -> PTProcess:
    """Start a PT server dispatcher."""
    env = {
        'TOR_PT_MANAGED_TRANSPORT_VER': '1',
        'TOR_PT_SERVER_TRANSPORTS': transport,
        'TOR_PT_ORPORT': or_addr,
        'TOR_PT_STATE_LOCATION': _state_dir(),
    }
    if bind_addr:
        env['TOR_PT_SERVER_BINDADDR'] = f'{transport}-{bind_addr}'
    return PTProcess(['main.py'], env)


def launch_client(transport: str) -> PTProcess:
    """Start a PT client dispatcher."""
    env = {
        'TOR_PT_MANAGED_TRANSPORT_VER': '1',
        'TOR_PT_CLIENT_TRANSPORTS': transport,
        'TOR_PT_STATE_LOCATION': _state_dir(),
    }
    return PTProcess(['main.py'], env)


# ---------------------------------------------------------------------------
# MockORPort — echo server that stands in for Tor's ORPort
# ---------------------------------------------------------------------------

class MockORPort:
    """
    A trivial TCP echo server that collects received bytes and lets the test
    inspect / control what gets sent back.

    ``received`` accumulates every byte the server reads across all connections.
    ``send_queue`` lets the test inject bytes to send back on the next
    accepted connection.
    """

    def __init__(self):
        self.received: bytes = b''
        self._lock = threading.Lock()
        self._received_event = threading.Event()
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind(('127.0.0.1', 0))
        self._srv.listen(16)
        self._srv.settimeout(1.0)
        self.addr: str = '127.0.0.1:{}'.format(self._srv.getsockname()[1])
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        # Each accepted connection's handler can receive a response to send back
        self._pending_responses: queue.Queue[bytes] = queue.Queue()

    def queue_response(self, data: bytes) -> None:
        """Enqueue bytes to send back on the next (or current) connection."""
        self._pending_responses.put(data)

    def wait_received(self, n_bytes: int, timeout: float = 5.0,
                      after: int = 0) -> bytes:
        """
        Block until at least *n_bytes* have been accumulated *after* byte
        offset *after*, then return all accumulated bytes from that offset.

        Pass ``after=len(orp.received)`` before sending to isolate each test
        from bytes accumulated by earlier tests on the same shared ORPort.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                window = self.received[after:]
                if len(window) >= n_bytes:
                    return window
            self._received_event.wait(timeout=0.05)
            self._received_event.clear()
        with self._lock:
            window = self.received[after:]
        raise TimeoutError(
            f"MockORPort: waited {timeout}s but only got {len(window)} "
            f"of {n_bytes} expected bytes after offset {after}"
        )

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(1.0)
        # Send any pre-queued response
        try:
            resp = self._pending_responses.get_nowait()
            conn.sendall(resp)
        except queue.Empty:
            pass
        # Echo all received data back
        while not self._stop.is_set():
            try:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                with self._lock:
                    self.received += chunk
                self._received_event.set()
                conn.sendall(chunk)   # echo
            except socket.timeout:
                continue
            except OSError:
                break
        try:
            conn.close()
        except OSError:
            pass

    def stop(self) -> None:
        self._stop.set()
        try:
            self._srv.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.stop()


# ---------------------------------------------------------------------------
# SOCKS5 client helper — synchronous, no external deps
# ---------------------------------------------------------------------------

def socks5_connect(proxy_addr: str, target_host: str, target_port: int,
                   timeout: float = 5.0) -> socket.socket:
    """
    Open a SOCKS5 connection through *proxy_addr* ("host:port") to
    *target_host*:*target_port*.

    Returns a connected socket ready for data transfer.
    """
    ph, pp = proxy_addr.rsplit(':', 1)
    sock = socket.create_connection((ph, int(pp)), timeout=timeout)

    # Method negotiation: request NO_AUTH (0x00)
    sock.sendall(b'\x05\x01\x00')
    resp = _recv_exact(sock, 2)
    assert resp == b'\x05\x00', f"unexpected method selection: {resp!r}"

    # CONNECT request with ATYP=DOMAIN
    host_bytes = target_host.encode('ascii')
    port_bytes = struct.pack('>H', target_port)
    req = (
        b'\x05\x01\x00'         # VER CMD RSV
        + b'\x03'               # ATYP = DOMAIN
        + bytes([len(host_bytes)])
        + host_bytes
        + port_bytes
    )
    sock.sendall(req)

    # Read reply: VER REP RSV ATYP  then address  then port
    hdr = _recv_exact(sock, 4)
    assert hdr[0] == 5, f"bad SOCKS5 reply version: {hdr!r}"
    assert hdr[1] == 0, f"SOCKS5 CONNECT failed, REP=0x{hdr[1]:02x}"
    atyp = hdr[3]
    if atyp == 0x01:   # IPv4
        _recv_exact(sock, 4 + 2)
    elif atyp == 0x03:  # DOMAIN
        dlen = _recv_exact(sock, 1)[0]
        _recv_exact(sock, dlen + 2)
    elif atyp == 0x04:  # IPv6
        _recv_exact(sock, 16 + 2)

    return sock


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError(f"socket closed after {len(buf)}/{n} bytes")
        buf += chunk
    return buf


def _recv_at_least(sock: socket.socket, n: int, timeout: float = 5.0) -> bytes:
    """Receive until at least *n* bytes accumulated or timeout."""
    sock.settimeout(timeout)
    buf = b''
    deadline = time.monotonic() + timeout
    while len(buf) < n and time.monotonic() < deadline:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
    return buf


# ===========================================================================
# Unit tests — FoobarTransport
# ===========================================================================

class TestFoobarUnit(unittest.TestCase):
    """Pure in-process unit tests for the foobar transport codec."""

    def setUp(self):
        # Import fresh so registry is populated
        sys.path.insert(0, str(PT_DIR))
        import transports  # noqa: F401  — registers transport
        from transport import create
        self.t = create('foobar')

    # ── contracts ──────────────────────────────────────────────────────────

    def test_encode_empty_returns_empty(self):
        self.assertEqual(self.t.encode(b''), b'')

    def test_decode_empty_returns_empty_and_empty_remainder(self):
        out, rem = self.t.decode(b'')
        self.assertEqual(out, b'')
        self.assertEqual(rem, b'')

    # ── size invariant ─────────────────────────────────────────────────────

    def test_encode_output_size(self):
        for n in (1, 2, 7, 8, 9, 255, 256):
            with self.subTest(n=n):
                # Build n bytes cycling through 0x01–0xff (never empty)
                data = (bytes(range(1, 256)) * (n // 255 + 1))[:n]
                enc = self.t.encode(data)
                self.assertEqual(len(enc), n * 24,
                                 f"encode({n} bytes) produced {len(enc)} bytes, expected {n*24}")

    # ── roundtrip ──────────────────────────────────────────────────────────

    def test_roundtrip_all_256_byte_values(self):
        """Every possible byte value survives encode → decode."""
        data = bytes(range(256))
        enc = self.t.encode(data)
        dec, rem = self.t.decode(enc)
        self.assertEqual(dec, data)
        self.assertEqual(rem, b'')

    def test_roundtrip_single_byte_zero(self):
        self._roundtrip(b'\x00')

    def test_roundtrip_single_byte_ff(self):
        self._roundtrip(b'\xff')

    def test_roundtrip_ascii_string(self):
        self._roundtrip(b'Hello, PT!')

    def test_roundtrip_binary_blob(self):
        import os
        data = os.urandom(512)
        self._roundtrip(data)

    def _roundtrip(self, data: bytes) -> None:
        enc = self.t.encode(data)
        dec, rem = self.t.decode(enc)
        self.assertEqual(dec, data)
        self.assertEqual(rem, b'')

    # ── partial-frame buffering ─────────────────────────────────────────────

    def test_decode_returns_remainder_for_partial_frame(self):
        """A buffer that doesn't fill a complete 24-byte frame is returned as remainder."""
        enc = self.t.encode(b'A')   # 24 bytes exactly
        for cut in (1, 3, 12, 23):
            with self.subTest(cut=cut):
                out, rem = self.t.decode(enc[:cut])
                self.assertEqual(out, b'')
                self.assertEqual(rem, enc[:cut])

    def test_decode_partial_then_complete(self):
        """Feeding partial + remainder + rest correctly reconstructs the original."""
        data = b'XY'
        enc = self.t.encode(data)   # 48 bytes
        # Feed first 30 bytes (one complete frame + 6 leftover)
        out1, rem1 = self.t.decode(enc[:30])
        self.assertEqual(out1, b'X')
        self.assertEqual(len(rem1), 6)
        # Feed remainder + rest
        out2, rem2 = self.t.decode(rem1 + enc[30:])
        self.assertEqual(out2, b'Y')
        self.assertEqual(rem2, b'')

    def test_decode_byte_by_byte(self):
        """Feeding one byte at a time must produce output only on the 24th byte."""
        data = b'\xab'
        enc = self.t.encode(data)
        self.assertEqual(len(enc), 24)
        buf = b''
        decoded = b''
        for i, byte in enumerate(enc):
            buf += bytes([byte])
            out, buf = self.t.decode(buf)
            decoded += out
        self.assertEqual(decoded, data)
        self.assertEqual(buf, b'')

    # ── token content ──────────────────────────────────────────────────────

    def test_encoded_bytes_are_only_foo_and_bar_tokens(self):
        """Every 3-byte token in the encoded output must be b'foo' or b'bar'."""
        enc = self.t.encode(bytes(range(256)))
        self.assertEqual(len(enc) % 3, 0)
        for i in range(0, len(enc), 3):
            token = enc[i:i+3]
            self.assertIn(token, (b'foo', b'bar'),
                          f"unexpected token {token!r} at offset {i}")

    def test_encode_0xff_is_all_foo(self):
        self.assertEqual(self.t.encode(b'\xff'), b'foo' * 8)

    def test_encode_0x00_is_all_bar(self):
        self.assertEqual(self.t.encode(b'\x00'), b'bar' * 8)

    def test_encode_msb_first(self):
        # 0xAB = 0b10101011 → foo bar foo bar foo bar foo foo
        expected = b'foobarfoobarfoobarfoofoo'
        self.assertEqual(self.t.encode(b'\xab'), expected)


# ===========================================================================
# IPC stdout tests
# ===========================================================================

class TestIPCServer(unittest.TestCase):
    """PT server mode: verify IPC lines emitted to stdout."""

    def test_version_line_emitted(self):
        with MockORPort() as orp, launch_server('foobar', orp.addr) as pt:
            line = pt.wait_for_line('VERSION')
            self.assertTrue(line.startswith('VERSION '), line)

    def test_smethod_line_format(self):
        """SMETHOD <transport> <host>:<port>"""
        with MockORPort() as orp, launch_server('foobar', orp.addr) as pt:
            line = pt.wait_for_line('SMETHOD foobar ')
            parts = line.split()
            self.assertEqual(parts[0], 'SMETHOD')
            self.assertEqual(parts[1], 'foobar')
            host, port_str = parts[2].rsplit(':', 1)
            self.assertTrue(port_str.isdigit(), f"port not numeric: {port_str!r}")
            self.assertGreater(int(port_str), 0)

    def test_smethods_done_emitted(self):
        with MockORPort() as orp, launch_server('foobar', orp.addr) as pt:
            pt.wait_for_line('SMETHODS DONE')

    def test_ipc_order_version_before_smethod_before_done(self):
        with MockORPort() as orp, launch_server('foobar', orp.addr) as pt:
            pt.wait_for_line('SMETHODS DONE')
            lines = pt.all_stdout()
            keywords = [l.split()[0] for l in lines if l.strip()]
            self.assertIn('VERSION',      keywords)
            self.assertIn('SMETHOD',      keywords)
            self.assertIn('SMETHODS',     keywords)   # "SMETHODS DONE"
            vi = next(i for i, k in enumerate(keywords) if k == 'VERSION')
            si = next(i for i, k in enumerate(keywords) if k == 'SMETHOD')
            di = next(i for i, k in enumerate(keywords) if k == 'SMETHODS')
            self.assertLess(vi, si, "VERSION must precede SMETHOD")
            self.assertLess(si, di, "SMETHOD must precede SMETHODS DONE")

    def test_no_error_lines_on_valid_config(self):
        with MockORPort() as orp, launch_server('foobar', orp.addr) as pt:
            pt.wait_for_line('SMETHODS DONE')
            lines = pt.all_stdout()
            for line in lines:
                for err_kw in ('ENV-ERROR', 'VERSION-ERROR', 'SMETHOD-ERROR'):
                    self.assertFalse(line.startswith(err_kw),
                                     f"unexpected error line: {line!r}")

    def test_unknown_transport_silently_skipped(self):
        """
        Unknown transports must NOT produce SMETHOD-ERROR — they are silently
        skipped per PT spec §3.3.  SMETHODS DONE is still emitted.
        """
        with MockORPort() as orp, launch_server('does_not_exist', orp.addr) as pt:
            pt.wait_for_line('SMETHODS DONE')
            lines = pt.all_stdout()
            for line in lines:
                self.assertFalse(line.startswith('SMETHOD-ERROR'),
                                 f"spec violation — unknown transport produced error: {line!r}")

    def test_missing_orport_emits_env_error(self):
        """Server mode without an ORPort must emit ENV-ERROR and exit non-zero."""
        env = {
            'TOR_PT_MANAGED_TRANSPORT_VER': '1',
            'TOR_PT_SERVER_TRANSPORTS': 'foobar',
            'TOR_PT_STATE_LOCATION': _state_dir(),
            # TOR_PT_ORPORT deliberately omitted
        }
        pt = PTProcess(['main.py'], env, timeout=5.0)
        pt.wait_for_line('ENV-ERROR')
        code = pt.wait(timeout=5.0)
        self.assertNotEqual(code, 0, "process should exit non-zero after ENV-ERROR")

    def test_bind_to_specific_port(self):
        """-bindaddr / TOR_PT_SERVER_BINDADDR should be honoured."""
        port = _free_port()
        with MockORPort() as orp:
            bind_addr = f'127.0.0.1:{port}'
            with launch_server('foobar', orp.addr, bind_addr=bind_addr) as pt:
                line = pt.wait_for_line('SMETHOD foobar ')
                _, _, addr_part = line.split(None, 2)
                reported_port = int(addr_part.split(':')[1])
                self.assertEqual(reported_port, port,
                                 f"PT server bound to wrong port: {line!r}")


class TestIPCClient(unittest.TestCase):
    """PT client mode: verify IPC lines emitted to stdout."""

    def test_version_line_emitted(self):
        with launch_client('foobar') as pt:
            line = pt.wait_for_line('VERSION')
            self.assertTrue(line.startswith('VERSION '), line)

    def test_cmethod_line_format(self):
        """CMETHOD <transport> socks5 <host>:<port>"""
        with launch_client('foobar') as pt:
            line = pt.wait_for_line('CMETHOD foobar ')
            parts = line.split()
            self.assertEqual(parts[0], 'CMETHOD')
            self.assertEqual(parts[1], 'foobar')
            self.assertEqual(parts[2], 'socks5')
            host, port_str = parts[3].rsplit(':', 1)
            self.assertTrue(port_str.isdigit(), f"port not numeric: {port_str!r}")
            self.assertGreater(int(port_str), 0)

    def test_cmethod_binds_to_loopback(self):
        """Client listeners must bind to 127.0.0.1 per spec."""
        with launch_client('foobar') as pt:
            line = pt.wait_for_line('CMETHOD foobar socks5 ')
            addr = line.split()[3]
            host = addr.rsplit(':', 1)[0]
            self.assertEqual(host, '127.0.0.1',
                             f"client listener not on loopback: {line!r}")

    def test_cmethods_done_emitted(self):
        with launch_client('foobar') as pt:
            pt.wait_for_line('CMETHODS DONE')

    def test_ipc_order_version_before_cmethod_before_done(self):
        with launch_client('foobar') as pt:
            pt.wait_for_line('CMETHODS DONE')
            lines = pt.all_stdout()
            keywords = [l.split()[0] for l in lines if l.strip()]
            vi = next(i for i, k in enumerate(keywords) if k == 'VERSION')
            ci = next(i for i, k in enumerate(keywords) if k == 'CMETHOD')
            di = next(i for i, k in enumerate(keywords) if k == 'CMETHODS')
            self.assertLess(vi, ci)
            self.assertLess(ci, di)

    def test_no_error_lines_on_valid_config(self):
        with launch_client('foobar') as pt:
            pt.wait_for_line('CMETHODS DONE')
            for line in pt.all_stdout():
                for err_kw in ('ENV-ERROR', 'VERSION-ERROR', 'CMETHOD-ERROR'):
                    self.assertFalse(line.startswith(err_kw),
                                     f"unexpected error line: {line!r}")

    def test_unknown_transport_silently_skipped(self):
        env = {
            'TOR_PT_MANAGED_TRANSPORT_VER': '1',
            'TOR_PT_CLIENT_TRANSPORTS': 'does_not_exist',
            'TOR_PT_STATE_LOCATION': _state_dir(),
        }
        with PTProcess(['main.py'], env) as pt:
            pt.wait_for_line('CMETHODS DONE')
            for line in pt.all_stdout():
                self.assertFalse(line.startswith('CMETHOD-ERROR'),
                                 f"spec violation: {line!r}")

    def test_multiple_transports_one_unknown(self):
        """
        When multiple transports are requested and one is unknown, the known
        one gets a CMETHOD line and the unknown one is silently skipped.
        """
        env = {
            'TOR_PT_MANAGED_TRANSPORT_VER': '1',
            'TOR_PT_CLIENT_TRANSPORTS': 'foobar,does_not_exist',
            'TOR_PT_STATE_LOCATION': _state_dir(),
        }
        with PTProcess(['main.py'], env) as pt:
            pt.wait_for_line('CMETHODS DONE')
            lines = pt.all_stdout()
            cmethod_lines = [l for l in lines if l.startswith('CMETHOD ')]
            self.assertEqual(len(cmethod_lines), 1,
                             f"expected exactly one CMETHOD line, got: {cmethod_lines}")
            self.assertIn('foobar', cmethod_lines[0])
            for l in lines:
                self.assertFalse(l.startswith('CMETHOD-ERROR'), l)


# ===========================================================================
# Lifecycle tests
# ===========================================================================

class TestLifecycle(unittest.TestCase):

    def test_server_sigterm_clean_exit(self):
        with MockORPort() as orp:
            pt = launch_server('foobar', orp.addr)
            pt.wait_for_line('SMETHODS DONE')
            code = pt.terminate(wait=5.0)
            # Accept 0 (clean) or negative SIGTERM value
            self.assertIn(code, (0, -signal.SIGTERM),
                          f"unexpected exit code after SIGTERM: {code}")

    def test_client_sigterm_clean_exit(self):
        pt = launch_client('foobar')
        pt.wait_for_line('CMETHODS DONE')
        code = pt.terminate(wait=5.0)
        self.assertIn(code, (0, -signal.SIGTERM),
                      f"unexpected exit code after SIGTERM: {code}")

    def test_client_stdin_eof_clean_exit(self):
        """Closing stdin (simulating Tor shutdown) must cause the PT to exit."""
        pt = launch_client('foobar')
        pt.wait_for_line('CMETHODS DONE')
        pt.close_stdin()
        code = pt.wait(timeout=8.0)
        self.assertIn(code, (0, -signal.SIGTERM),
                      f"unexpected exit code after stdin EOF: {code}")

    def test_server_stdin_eof_clean_exit(self):
        with MockORPort() as orp:
            pt = launch_server('foobar', orp.addr)
            pt.wait_for_line('SMETHODS DONE')
            pt.close_stdin()
            code = pt.wait(timeout=8.0)
            self.assertIn(code, (0, -signal.SIGTERM),
                          f"unexpected exit code after stdin EOF: {code}")

    def test_no_stderr_output_on_clean_run(self):
        """
        With default log level (WARNING) there should be no stderr output
        during a normal startup + SIGTERM sequence.
        """
        with MockORPort() as orp:
            pt = launch_server('foobar', orp.addr)
            pt.wait_for_line('SMETHODS DONE')
            pt.terminate()
            # Read stderr; give the process a moment to flush
            assert pt.proc.stderr is not None
            pt.proc.stderr.settimeout = lambda _: None  # type: ignore
            try:
                stderr = pt.proc.stderr.read(4096)
            except Exception:
                stderr = b''
            # Filter out any asyncio deprecation warnings about get_event_loop
            lines = [l for l in stderr.decode(errors='replace').splitlines()
                     if l.strip() and 'DeprecationWarning' not in l]
            self.assertEqual(lines, [],
                             f"unexpected stderr output: {stderr!r}")


# ===========================================================================
# End-to-end data flow tests
# ===========================================================================

class TestEndToEnd(unittest.TestCase):
    """
    Full stack: MockORPort ← PT server ← (foobar wire) ← PT client ← SOCKS5 client

    Test fixture starts both PT processes and a mock ORPort, waits for all
    IPC DONE lines, then runs individual data-flow assertions.
    """

    @classmethod
    def setUpClass(cls):
        cls.orp = MockORPort()

        cls.pt_server = launch_server('foobar', cls.orp.addr)
        smethod_line = cls.pt_server.wait_for_line('SMETHOD foobar ')
        # parse "SMETHOD foobar host:port"
        cls.bridge_addr = smethod_line.split()[2]   # host:port the PT server listens on
        cls.pt_server.wait_for_line('SMETHODS DONE')

        cls.pt_client = launch_client('foobar')
        cmethod_line = cls.pt_client.wait_for_line('CMETHOD foobar socks5 ')
        cls.socks5_addr = cmethod_line.split()[3]   # host:port of SOCKS5 listener
        cls.pt_client.wait_for_line('CMETHODS DONE')

        # Extract bridge host/port for SOCKS5 CONNECT target
        cls.bridge_host, bp = cls.bridge_addr.rsplit(':', 1)
        cls.bridge_port = int(bp)

    @classmethod
    def tearDownClass(cls):
        cls.pt_client.terminate()
        cls.pt_server.terminate()
        cls.orp.stop()

    def _connect(self) -> socket.socket:
        """Open a fresh SOCKS5 connection through the PT client to the PT server."""
        return socks5_connect(
            self.socks5_addr,
            self.bridge_host,
            self.bridge_port,
        )

    # ── data flow ──────────────────────────────────────────────────────────

    def test_client_to_server_data_arrives_at_orport(self):
        """
        Bytes sent by the SOCKS5 client must arrive plaintext at the mock ORPort.
        """
        payload = b'Hello, ORPort!'
        # Snapshot how many bytes the ORPort already holds from earlier tests
        offset = len(self.orp.received)
        sock = self._connect()
        try:
            sock.sendall(payload)
            received = self.orp.wait_received(len(payload), after=offset)
            self.assertIn(payload, received,
                          f"payload not found in ORPort data: {received!r}")
        finally:
            sock.close()

    def test_server_to_client_data_arrives_at_socks5_client(self):
        """
        Bytes sent by the mock ORPort must arrive plaintext at the SOCKS5 client.
        The mock ORPort echoes everything it receives, so we send from the client
        and verify we get the same bytes back.
        """
        payload = b'Ping!'
        sock = self._connect()
        try:
            sock.sendall(payload)
            # ORPort echoes — wait for the echo to arrive back
            reply = _recv_at_least(sock, len(payload), timeout=5.0)
            self.assertEqual(reply, payload,
                             f"echo mismatch: sent {payload!r}, got {reply!r}")
        finally:
            sock.close()

    def test_bidirectional_roundtrip(self):
        """Larger payload survives the full encode→wire→decode→ORPort→encode→wire→decode chain."""
        import os
        payload = os.urandom(256)
        sock = self._connect()
        try:
            sock.sendall(payload)
            reply = _recv_at_least(sock, len(payload), timeout=8.0)
            self.assertEqual(reply, payload,
                             "roundtrip payload mismatch")
        finally:
            sock.close()

    def test_multiple_sequential_connections(self):
        """Each connection is independent; the transport must stay alive between them."""
        for i in range(3):
            with self.subTest(connection=i):
                msg = f'connection {i}'.encode()
                sock = self._connect()
                try:
                    sock.sendall(msg)
                    reply = _recv_at_least(sock, len(msg), timeout=5.0)
                    self.assertEqual(reply, msg)
                finally:
                    sock.close()

    def test_empty_payload_does_not_crash(self):
        """
        Opening a SOCKS5 connection and immediately closing it must not
        crash either PT process.
        """
        sock = self._connect()
        sock.close()
        # Give the relay a moment to clean up, then check both PT procs are alive
        time.sleep(0.3)
        self.assertIsNone(self.pt_client.proc.poll(),
                          "PT client crashed after empty connection")
        self.assertIsNone(self.pt_server.proc.poll(),
                          "PT server crashed after empty connection")

    def test_ipc_lines_valid_after_connections(self):
        """
        After data flows, re-inspect stdout: no error lines should have appeared.
        """
        # Do one roundtrip to ensure some traffic has occurred
        sock = self._connect()
        sock.sendall(b'check')
        _recv_at_least(sock, 5, timeout=3.0)
        sock.close()
        time.sleep(0.2)

        for label, pt in (('client', self.pt_client), ('server', self.pt_server)):
            for line in pt.all_stdout():
                for err in ('ENV-ERROR', 'VERSION-ERROR', 'CMETHOD-ERROR', 'SMETHOD-ERROR'):
                    self.assertFalse(line.startswith(err),
                                     f"PT {label} emitted error after traffic: {line!r}")


# ===========================================================================
# Parameterised transport name helper
# ===========================================================================

def make_transport_tests(transport_name: str):
    """
    Return a TestCase subclass that runs the full IPC + lifecycle + data-flow
    suite against the named transport.

    Usage in conftest or test file::

        TestFoobarE2E = make_transport_tests('foobar')

    This makes it easy to add tests for a new transport: just call this
    function with the transport's registered name.
    """

    class _TransportTests(unittest.TestCase):
        TRANSPORT = transport_name

        def test_server_ipc(self):
            with MockORPort() as orp, \
                 launch_server(self.TRANSPORT, orp.addr) as pt:
                pt.wait_for_line('SMETHODS DONE')
                lines = pt.all_stdout()
                self.assertTrue(any(l.startswith(f'SMETHOD {self.TRANSPORT}') for l in lines),
                                f"no SMETHOD line for {self.TRANSPORT}: {lines}")

        def test_client_ipc(self):
            with launch_client(self.TRANSPORT) as pt:
                pt.wait_for_line('CMETHODS DONE')
                lines = pt.all_stdout()
                self.assertTrue(
                    any(l.startswith(f'CMETHOD {self.TRANSPORT} socks5') for l in lines),
                    f"no CMETHOD line for {self.TRANSPORT}: {lines}")

        def test_e2e_roundtrip(self):
            with MockORPort() as orp:
                with launch_server(self.TRANSPORT, orp.addr) as pts:
                    smethod = pts.wait_for_line(f'SMETHOD {self.TRANSPORT} ')
                    bridge_addr = smethod.split()[2]
                    bh, bp = bridge_addr.rsplit(':', 1)
                    pts.wait_for_line('SMETHODS DONE')

                    with launch_client(self.TRANSPORT) as ptc:
                        cmethod = ptc.wait_for_line(f'CMETHOD {self.TRANSPORT} socks5 ')
                        socks_addr = cmethod.split()[3]
                        ptc.wait_for_line('CMETHODS DONE')

                        payload = b'roundtrip test for ' + self.TRANSPORT.encode()
                        sock = socks5_connect(socks_addr, bh, int(bp))
                        try:
                            sock.sendall(payload)
                            reply = _recv_at_least(sock, len(payload), timeout=8.0)
                            self.assertEqual(reply, payload)
                        finally:
                            sock.close()

    _TransportTests.__name__ = f'TestTransport_{transport_name}'
    _TransportTests.__qualname__ = _TransportTests.__name__
    return _TransportTests


# Register parameterised suite for foobar (and any future transports here)
TestFoobar_Parameterised = make_transport_tests('foobar')


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)