from typing import Protocol, runtime_checkable

@runtime_checkable
class UidMessage(Protocol):
    uid: str
