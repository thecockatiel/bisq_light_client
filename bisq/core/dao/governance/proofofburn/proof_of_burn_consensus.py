from io import BytesIO
from typing import TYPE_CHECKING
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.setup.log_setup import get_logger
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.dao.governance.asset.stateful_asset import StatefulAsset
    from bisq.core.dao.state.dao_state_service import DaoStateService


class ProofOfBurnConsensus:
    @staticmethod
    def get_hash(bytes: bytes) -> bytes:
        return get_sha256_ripemd160_hash(bytes)

    @staticmethod
    def get_op_return_data(hash: bytes) -> bytes:
        with BytesIO() as output_stream:
            output_stream.write(OpReturnType.PROOF_OF_BURN.type)
            output_stream.write(Version.PROOF_OF_BURN)
            output_stream.write(hash)
            return output_stream.getvalue()

    @staticmethod
    def has_op_return_data_valid_length(op_return_data: bytes) -> bool:
        return len(op_return_data) == 22

    @staticmethod
    def get_hash_from_op_return_data(op_return_data: bytes) -> bytes:
        return op_return_data[2:22]
