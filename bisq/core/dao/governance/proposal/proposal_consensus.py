from io import BytesIO
from typing import TYPE_CHECKING, Union
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.core.dao.governance.param.param import Param

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal


class ProposalConsensus:
    """Encapsulates consensus critical aspects."""

    @staticmethod
    def get_fee(dao_state_service: "DaoStateService", chain_height: int):
        return dao_state_service.get_param_value_as_coin(
            Param.PROPOSAL_FEE, chain_height
        )

    @staticmethod
    def get_hash_of_payload(payload: "Proposal") -> bytes:
        bytes_to_hash = payload.serialize_for_hash()
        return get_sha256_ripemd160_hash(bytes_to_hash)

    @staticmethod
    def get_op_return_data(
        hash_of_payload: bytes, op_return_type: bytes, version: bytes
    ) -> bytes:
        with BytesIO() as output_stream:
            output_stream.write(op_return_type)
            output_stream.write(version)
            output_stream.write(hash_of_payload)
            return output_stream.getvalue()

    @staticmethod
    def has_op_return_data_valid_length(op_return_data: bytes) -> bool:
        return len(op_return_data) == 22
