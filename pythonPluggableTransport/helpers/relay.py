# The relay manages two concurrent pump tasks:

#   A -encode> B (plain output; no buffering needed)
#   B -decode> A (framed output; partial frames are buffered)

# For the PT client:
#   A = Tor side (SOCKS5 client), B = PT bridge side
#   A->B: encode plaintext before sending to bridge
#   B->A: decode ciphertext arriving from bridge

# For the PT bridge:
#   A = PT client side, B = ORPort side
#   A->B: decode ciphertext arriving from PT client
#   B->A: encode plaintext before sending back to PT client

# The caller chooses which direction uses encode and which uses decode by
# passing the appropriate callables; the relay itself is direction-agnostic.

import asyncio
import logging
from typing import Callable, Tuple

log = logging.getLogger(__name__)

CHUNK = 65536  # bytes per read() call


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    # Flush any buffered output, then close the writer.

    # Calling writer.close() without a prior drain() can silently drop data that has been write()-buffered but not yet handed to the kernel. We drain first, tolerating any error (the peer may already be gone), then close and wait for the underlying transport to finish its teardown.

    try:
        await writer.drain()
    except Exception:
        pass
    try:
        if not writer.is_closing():
            writer.close()
        await writer.wait_closed()
    except Exception:
        pass


async def _pump_encode(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    encode_fn: Callable[[bytes], bytes],
) -> None:
    # Pump bytes from reader to writer, passing each chunk through encode_fn
    try:
        while True:
            chunk = await reader.read(CHUNK)
            if not chunk:
                break
            transformed = encode_fn(chunk)
            if transformed:
                writer.write(transformed)
                await writer.drain()
    except (
        asyncio.IncompleteReadError,
        ConnectionResetError,
        BrokenPipeError,
        OSError,
    ) as exc:
        log.debug("pump_encode EOF/error: %s", exc)
    finally:
        await _close_writer(writer)


async def _pump_decode(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    decode_fn: Callable[[bytes], Tuple[bytes, bytes]],
) -> None:
    # Pump bytes from reader to writer, passing the accumulated buffer through decode_fn which may return partial output.
    # decode_fn(buf) -> (decoded_bytes, remaining_buf)
    # remaining_buf is fed into the next decode call so no frame boundaries are ever lost between read() calls.

    buf = b""
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
    except (
        asyncio.IncompleteReadError,
        ConnectionResetError,
        BrokenPipeError,
        OSError,
        ValueError,
    ) as exc:
        # ValueError is included because transport decode() implementations
        # may raise it for malformed frames; we log and close cleanly rather
        # than letting the exception escape and silently kill the connection.
        log.debug("pump_decode EOF/error: %s", exc)
    finally:
        await _close_writer(writer)


# a_to_b_fn -> en-/decode function for direction A -> B
# a_to_b_is_decode -> if true, then a_to_b_fn is a decode function
# b_to_a_fn -> en-/decode function for direction B -> A
# b_to_a_is_decode -> if true, then b_to_a_fn is a decode function
async def relay(
    a_reader: asyncio.StreamReader,
    a_writer: asyncio.StreamWriter,
    b_reader: asyncio.StreamReader,
    b_writer: asyncio.StreamWriter,
    *,
    a_to_b_fn: Callable,
    a_to_b_is_decode: bool = False,
    b_to_a_fn: Callable,
    b_to_a_is_decode: bool = False,
) -> None:
    # Run two pump tasks concurrently until both sides close.
    # Each pump closes its writer in its finally block, which propagates an EOF to the peer's reader, causing the other pump to exit naturally. Just wait for ALL_COMPLETED: there is no need to cancel either task because they will both terminate once the underlying connections close.
    # Using FIRST_COMPLETED here would not work: when one pump finishes (e.g. the ORPort closes after sending its response), the other pump would be cancelled before it could forward the in-flight reply, producing empty packets on the wire.

    # Typical usage for PT client mode::
    #     await relay(tor_reader, tor_writer, srv_reader, srv_writer, a_to_b_fn=transport.encode,   a_to_b_is_decode=False, b_to_a_fn=transport.decode,   b_to_a_is_decode=True)

    # Typical usage for PT bridge mode::
    #     await relay(client_reader, client_writer, or_reader, or_writer, a_to_b_fn=transport.decode, a_to_b_is_decode=True, b_to_a_fn=transport.encode, b_to_a_is_decode=False)

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

    # Wait for BOTH pumps to finish.

    # Half-close propagation guarantees termination without an explicit cancellation
    await asyncio.wait(
        [task_a_b, task_b_a],
        return_when=asyncio.ALL_COMPLETED,
    )
