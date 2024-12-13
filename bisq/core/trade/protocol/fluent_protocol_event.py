from typing import Protocol, runtime_checkable

@runtime_checkable
class FluentProtocolEvent(Protocol):
    name: str