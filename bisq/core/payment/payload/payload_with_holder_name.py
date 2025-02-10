from typing import Protocol, runtime_checkable


@runtime_checkable
class PayloadWithHolderName(Protocol):
    holder_name: str
