"""
relay.py — Bidirectional async relay with pluggable encode/decode transforms

The relay manages two concurrent pump tasks:

  A ──encode──► B      (plain output; no buffering needed)
  B ──decode──► A      (framed output; partial frames are buffered)

For the PT client:
  A = Tor side (SOCKS5 client),  B = PT server side
  A→B: encode plaintext before sending to server
  B→A: decode ciphertext arriving from server

For the PT server:
  A = PT client side,             B = ORPort side
  A→B: decode ciphertext arriving from PT client
  B→A: encode plaintext before sending back to PT client

The caller chooses which direction uses encode and which uses decode by
passing the appropriate callables; the relay itself is direction-agnostic.
"""

import asyncio
import logging
from typing import Callable, Tuple

log = logging.getLogger(__name__)

CHUNK = 65536   # bytes per read() call


# ──────────────────────────────────────────────────────────────────────────────
# Internal one-direction pump
# ──────────────────────────────────────────────────────────────────────────────

async def _pump_encode(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    encode_fn: Callable[[bytes], bytes],
) -> None:
    """Pump bytes from reader to writer, passing each chunk through encode_fn."""
    try:
        while True:
            chunk = await reader.read(CHUNK)
            if not chunk:
                break
            transformed = encode_fn(chunk)
            if transformed:
                writer.write(transformed)
                await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionResetError,
            BrokenPipeError, OSError) as exc:
        log.debug("pump_encode EOF/error: %s", exc)
    finally:
        _close_quietly(writer)


async def _pump_decode(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    decode_fn: Callable[[bytes], Tuple[bytes, bytes]],
) -> None:
    """
    Pump bytes from reader to writer, passing the accumulated buffer through
    decode_fn which may return partial output.

    decode_fn(buf) → (decoded_bytes, remaining_buf)
    remaining_buf is fed into the next decode call so no frame boundaries
    are ever lost between read() calls.
    """
    buf = b''
    try:
        while True:
            chunk = await reader.read(CHUNK)
            if not chunk:
                break
            buf += chunk
            decoded, buf = decode_fn(buf)
            if decoded:
                writer.write(decoded)
                await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionResetError,
            BrokenPipeError, OSError) as exc:
        log.debug("pump_decode EOF/error: %s", exc)
    finally:
        _close_quietly(writer)


def _close_quietly(writer: asyncio.StreamWriter) -> None:
    try:
        if not writer.is_closing():
            writer.close()
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

async def relay(
    a_reader: asyncio.StreamReader,
    a_writer: asyncio.StreamWriter,
    b_reader: asyncio.StreamReader,
    b_writer: asyncio.StreamWriter,
    *,
    a_to_b_fn: Callable,                    # encode_fn OR decode_fn for A→B direction
    a_to_b_is_decode: bool = False,         # True → a_to_b_fn is a decode_fn
    b_to_a_fn: Callable,                    # encode_fn OR decode_fn for B→A direction
    b_to_a_is_decode: bool = False,         # True → b_to_a_fn is a decode_fn
) -> None:
    """
    Run two pump tasks concurrently until either side closes.

    Typical usage for PT client mode::

        await relay(
            tor_reader, tor_writer,
            srv_reader, srv_writer,
            a_to_b_fn=transport.encode,   a_to_b_is_decode=False,
            b_to_a_fn=transport.decode,   b_to_a_is_decode=True,
        )

    Typical usage for PT server mode::

        await relay(
            client_reader, client_writer,
            or_reader,     or_writer,
            a_to_b_fn=transport.decode,   a_to_b_is_decode=True,
            b_to_a_fn=transport.encode,   b_to_a_is_decode=False,
        )
    """
    pump_a_b = (
        _pump_decode(a_reader, b_writer, a_to_b_fn)
        if a_to_b_is_decode
        else _pump_encode(a_reader, b_writer, a_to_b_fn)
    )
    pump_b_a = (
        _pump_decode(b_reader, a_writer, b_to_a_fn)
        if b_to_a_is_decode
        else _pump_encode(b_reader, a_writer, b_to_a_fn)
    )

    task_a_b = asyncio.create_task(pump_a_b)
    task_b_a = asyncio.create_task(pump_b_a)

    _done, pending = await asyncio.wait(
        [task_a_b, task_b_a],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
