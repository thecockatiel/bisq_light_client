from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.extended_data_size_permission import (
    ExtendedDataSizePermission,
)
from bisq.core.network.p2p.initial_data_response import InitialDataResponse

from utils.data import raise_required

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.model.state_hash import StateHash

_T = TypeVar("T", bound="StateHash")


@dataclass
class GetStateHashesResponse(
    Generic[_T],
    NetworkEnvelope,
    DirectMessage,
    ExtendedDataSizePermission,
    InitialDataResponse,
):
    state_hashes: list[_T] = field(default_factory=raise_required)
    request_nonce: int = field(default_factory=raise_required)

    def __str__(self):
        return (
            f"GetStateHashesResponse{{\n"
            f"    state_hashes={self.state_hashes},\n"
            f"    request_nonce={self.request_nonce}\n"
            f"}} {super().__str__()}"
        )
