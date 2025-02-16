from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from utils.concurrency import AtomicInt

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistable_envelope import (
        PersistableEnvelope,
    )
    from bisq.core.network.p2p.persistence.store_service import StoreService

_T = TypeVar("T", bound="PersistableEnvelope")


class ResourceDataStoreService:
    """Used for handling data from resource files."""

    def __init__(self):
        self._services: list["StoreService[_T]"] = []

    def add_service(self, service: "StoreService[_T]") -> None:
        self._services.append(service)

    def read_from_resources(
        self, post_fix: str, complete_handler: Callable[[], None]
    ) -> None:
        if not self._services:
            complete_handler()
            return
        remaining = AtomicInt(len(self._services))
        for service in self._services:
            service.read_from_resources(
                post_fix, lambda: self._on_read_complete(remaining, complete_handler)
            )

    def _on_read_complete(
        self, remaining: AtomicInt, complete_handler: Callable[[], None]
    ) -> None:
        if remaining.decrement_and_get() == 0:
            complete_handler()

    def read_from_resources_sync(self, post_fix: str) -> None:
        """Uses synchronous execution on the User Thread. Only used by tests. The async methods should be used by app code."""
        for service in self._services:
            service.read_from_resources_sync(post_fix)
