from dataclasses import dataclass, field
from typing import Set, Optional

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.extended_data_size_permission import ExtendedDataSizePermission
from bisq.core.network.p2p.initial_data_request import InitialDataRequest

@dataclass(frozen=True)
class GetDataRequest(NetworkEnvelope, ExtendedDataSizePermission, InitialDataRequest):
    nonce: int
    # Keys for ProtectedStorageEntry items to be excluded from the request because the peer has them already
    excluded_keys: Set[bytes]
    # Added at v1.4.0
    # The version of the requester. Used for response to send potentially missing historical data
    version: Optional[str] = field(default=None)