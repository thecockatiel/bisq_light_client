from abc import ABC
from typing import Generic, TypeVar
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.core.dao.monitoring.model.state_hash import StateHash
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)


_T = TypeVar("T", bound=StateHash)


class NewStateHashMessage(
    Generic[_T], BroadcastMessage, CapabilityRequiringPayload, ABC
):
    def __init__(self, state_hash: _T, message_version: int = None):
        if message_version is None:
            super().__init__()
        else:
            super().__init__(message_version)

        self.state_hash = state_hash

    def get_required_capabilities(self) -> Capabilities:
        return Capabilities([Capability.DAO_STATE])

    def __str__(self) -> str:
        return (
            f"NewStateHashMessage{{\n     stateHash={self.state_hash}\n}} "
            + super().__str__()
        )

    def __eq__(self, value):
        return (
            isinstance(value, NewStateHashMessage)
            and value.state_hash == self.state_hash
            and value.message_version == self.message_version
        )

    def __hash__(self):
        return hash(self.state_hash, self.message_version)
