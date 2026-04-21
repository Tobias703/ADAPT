# Adding a new transport requires only:
#   1. Subclass BaseTransport
#   2. Set a unique 'name' class attribute
#   3. Implement 'encode()' and 'decode()'
#   4. Decorate the class with @register and import it in transports/__init__.py)

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Type


class BaseTransport(ABC):
    # A new instance is created for every connection, so subclasses may safely maintain per-connection state (session keys, sequence numbers, …). Stateless transports (like foobar) simply ignore the instance state.

    #: Unique transport name used in torrc / PT IPC
    name: str = ""

    # encode
    @abstractmethod
    def encode(self, data: bytes) -> bytes:
        # Transform outgoing plaintext bytes into wire bytes.

        # Contract:
        #   - Must always return complete output - no internal buffering.
        #   - encode(b'') must return b'' (empty byte)
        #   - Calling code passes arbitrarily-sized chunks; encode each chunk independently and completely.
        ...

    # decode
    @abstractmethod
    def decode(self, buf: bytes) -> Tuple[bytes, bytes]:
        # Transform incoming wire bytes back to plaintext.

        # Contract:
        #   - May return partial output when 'buf' ends mid-frame.
        #   - Returns (decoded_output, remaining_buf) where 'remaining_buf' contains any bytes that could not yet form a complete frame.
        #   - decode(b'') must return (b'', b'')
        #   - The relay engine feeds 'remaining_buf' back into the next call automatically.
        ...


_REGISTRY: Dict[str, Type[BaseTransport]] = {}


def register(cls: Type[BaseTransport]) -> Type[BaseTransport]:
    # Class decorator that registers a transport.

    # Usage:
    #     @register
    #     class MyTransport(BaseTransport):
    #         name = "mytransport"
    #         …

    if not cls.name:
        raise ValueError(
            f"Transport class {cls.__name__!r} must define a non-empty 'name' attribute"
        )
    _REGISTRY[cls.name] = cls
    return cls


def create(name: str, **kwargs) -> BaseTransport:
    # Instantiate a fresh transport object by name.

    # Raises KeyError if the name is not registered.
    # kwargs are forwarded to the transport constructor (useful for options).

    if name not in _REGISTRY:
        raise KeyError(f"Unknown transport: {name!r}  (registered: {list(_REGISTRY)})")
    return _REGISTRY[name](**kwargs)


def available() -> list:
    # Return a list of all registered transport names
    return list(_REGISTRY.keys())


def is_registered(name: str) -> bool:
    return name in _REGISTRY
