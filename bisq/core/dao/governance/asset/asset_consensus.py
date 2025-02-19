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

logger = get_logger(__name__)


class AssetConsensus:
    @staticmethod
    def get_fee_per_day(
        dao_state_service: "DaoStateService", chain_height: int
    ) -> Coin:
        return dao_state_service.get_param_value_as_coin(
            Param.ASSET_LISTING_FEE_PER_DAY, chain_height
        )

    @staticmethod
    def get_hash(stateful_asset: "StatefulAsset") -> bytes:
        string_input = f"AssetListingFee-{stateful_asset.ticker_symbol}"
        bytes_input = string_input.encode("utf-8")
        return get_sha256_ripemd160_hash(bytes_input)

    @staticmethod
    def get_op_return_data(hash: bytes) -> bytes:
        with BytesIO() as output_stream:
            output_stream.write(bytes([OpReturnType.ASSET_LISTING_FEE.type]))
            output_stream.write(Version.ASSET_LISTING_FEE)
            output_stream.write(hash)
            return output_stream.getvalue()

    @staticmethod
    def has_op_return_data_valid_length(op_return_data: bytes) -> bool:
        return len(op_return_data) == 22
