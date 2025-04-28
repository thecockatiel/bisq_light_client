from dataclasses import dataclass
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.core.btc.exceptions.transaction_verification_exception import (
    TransactionVerificationException,
)
from bisq.core.btc.exceptions.wallet_exception import WalletException
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.governance.asset.asset_consensus import AssetConsensus
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.tx_exception import TxException
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.remove_asset_proposal import (
    RemoveAssetProposal,
)
from bisq.core.locale.currency_util import (
    get_currency_name_and_code,
    get_sorted_asset_stream,
)
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.dao.governance.asset.asset_state import AssetState
from datetime import timedelta

from utils.time import get_time_ms


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.dao.governance.asset.fee_payment import FeePayment
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.governance.asset.stateful_asset import StatefulAsset
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.util.coin.bsq_formatter import BsqFormatter


@dataclass(frozen=True)
class TradeAmountDateTuple:
    trade_amount: int
    trade_date: int


class AssetService(DaoSetupService, DaoStateListener):
    DEFAULT_LOOK_BACK_PERIOD_DAYS = 120  # 120 days

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        wallets_manager: "WalletsManager",
        trade_statistics_manager: "TradeStatisticsManager",
        dao_state_service: "DaoStateService",
        bsq_formatter: "BsqFormatter",
    ):
        self.logger = get_ctx_logger(__name__)
        self._bsq_wallet_service = bsq_wallet_service
        self._btc_wallet_service = btc_wallet_service
        self._wallets_manager = wallets_manager
        self._trade_statistics_manager = trade_statistics_manager
        self._dao_state_service = dao_state_service
        self._bsq_formatter = bsq_formatter

        # Only accessed via getter which fills the list on demand
        self._lazy_loaded_stateful_assets: list["StatefulAsset"] = []
        self._bsq_fee_per_day = 0
        self._min_volume_in_btc = 0

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._dao_state_service.add_dao_state_listener(self)

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        chain_height = self._dao_state_service.chain_height
        self._bsq_fee_per_day = self._dao_state_service.get_param_value_as_coin(
            Param.ASSET_LISTING_FEE_PER_DAY, chain_height
        ).value
        self._min_volume_in_btc = self._dao_state_service.get_param_value_as_coin(
            Param.ASSET_MIN_VOLUME, chain_height
        ).value

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_stateful_assets(self) -> list["StatefulAsset"]:
        if not self._lazy_loaded_stateful_assets:
            self._lazy_loaded_stateful_assets.extend(
                StatefulAsset(asset)
                for asset in get_sorted_asset_stream()
                if asset.get_ticker_symbol() != "BSQ"
            )
        return self._lazy_loaded_stateful_assets

    # Java Call takes about 22 ms. Should be only called on demand (e.g. view is showing the data)
    def update_asset_states(self):
        # For performance optimisation we map the trade stats to a temporary lookup map and convert it to a custom
        # TradeAmountDateTuple object holding only the data we need.
        lookup_map: dict[str, list[TradeAmountDateTuple]] = {}
        for e in self._trade_statistics_manager.observable_trade_statistics_set:
            if is_crypto_currency(e.currency):
                if e.currency not in lookup_map:
                    lookup_map[e.currency] = []
                lookup_map[e.currency].append(TradeAmountDateTuple(e.amount, e.date))

        for stateful_asset in self.get_stateful_assets():
            if stateful_asset.asset_state == AssetState.REMOVED_BY_VOTING:
                # if once set to REMOVED_BY_VOTING we ignore it for further processing
                continue

            ticker_symbol = stateful_asset.ticker_symbol
            if self._was_asset_removed_by_voting(ticker_symbol):
                stateful_asset.asset_state = AssetState.REMOVED_BY_VOTING
            else:
                stateful_asset.fee_payments = self._get_fee_payments(stateful_asset)
                look_back_period_in_days = self._get_look_back_period_in_days(
                    stateful_asset
                )
                stateful_asset.look_back_period_in_days = look_back_period_in_days
                lookup_date = get_time_ms() - int(
                    timedelta(days=look_back_period_in_days).total_seconds() * 1000
                )
                trade_volume = self._get_trade_volume(
                    lookup_date, lookup_map.get(ticker_symbol, None)
                )
                stateful_asset.trade_volume = trade_volume

                if self._is_in_trial_period(stateful_asset):
                    stateful_asset.asset_state = AssetState.IN_TRIAL_PERIOD
                elif trade_volume >= self._min_volume_in_btc:
                    stateful_asset.asset_state = AssetState.ACTIVELY_TRADED
                else:
                    stateful_asset.asset_state = AssetState.DE_LISTED

        lookup_map.clear()

    def is_active(self, ticker_symbol: str) -> bool:
        asset = self._find_asset(ticker_symbol)
        return asset.is_active if asset else False

    def pay_fee(
        self, stateful_asset: "StatefulAsset", listing_fee: int
    ) -> "Transaction":
        check_argument(
            not stateful_asset.was_removed_by_voting, "Asset must not have been removed"
        )
        check_argument(
            listing_fee >= self.get_fee_per_day().value,
            "Fee must not be less than listing fee for 1 day.",
        )
        check_argument(
            listing_fee % 100 == 0, "Fee must be a multiple of 1 BSQ (100 satoshi)."
        )
        try:
            # We create a prepared Bsq Tx for the listing fee.
            prepared_burn_fee_tx = (
                self._bsq_wallet_service.get_prepared_burn_fee_tx_for_asset_listing(
                    Coin.value_of(listing_fee)
                )
            )
            hash = AssetConsensus.get_hash(stateful_asset)
            op_return_data = AssetConsensus.get_op_return_data(hash)
            # We add the BTC inputs for the miner fee.
            tx_with_btc_fee = self._btc_wallet_service.complete_prepared_burn_bsq_tx(
                prepared_burn_fee_tx, op_return_data
            )
            # We sign the BSQ inputs of the final tx.
            transaction = self._bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
                tx_with_btc_fee
            )
            self.logger.info(f"Asset listing fee tx: {transaction}")
            return transaction
        except Exception as e:
            raise TxException(e)

    def get_fee_per_day(self) -> "Coin":
        return AssetConsensus.get_fee_per_day(
            self._dao_state_service, self._dao_state_service.chain_height
        )

    def publish_transaction(
        self,
        transaction: "Transaction",
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        class Callback(TxBroadcasterCallback):
            def on_success(self_, tx: "Transaction"):
                self.logger.info(
                    f"Asset listing fee tx has been published. TxId={tx.get_tx_id()}"
                )
                result_handler()

            def on_failure(self_, exception: Exception):
                error_message_handler(str(exception))

        self._wallets_manager.publish_and_commit_bsq_tx(
            transaction,
            TxType.ASSET_LISTING_FEE,
            Callback(),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Get the trade volume from lookupDate until current date
    def _get_trade_volume(
        self,
        lookup_date: int,
        trade_amount_date_tuple_list: Optional[list[TradeAmountDateTuple]],
    ) -> int:
        if trade_amount_date_tuple_list is None:
            # Was never traded
            return 0

        return sum(
            e.trade_amount
            for e in trade_amount_date_tuple_list
            if e.trade_date > lookup_date
        )

    def _is_in_trial_period(self, stateful_asset: "StatefulAsset") -> bool:
        for fee_payment in stateful_asset.fee_payments:
            passed_days = fee_payment.get_passed_days(self._dao_state_service)
            if passed_days is not None:
                days_covered_by_fee = fee_payment.days_covered_by_fee(
                    self._bsq_fee_per_day
                )
                if days_covered_by_fee >= passed_days:
                    return True
        return False

    def _get_look_back_period_in_days(self, stateful_asset: "StatefulAsset") -> int:
        # We need to use the block height of the fee payment tx not the current one as feePerDay might have been
        # changed in the meantime.
        last_fee_payment = stateful_asset.last_fee_payment
        if last_fee_payment:
            tx = self._dao_state_service.get_tx(last_fee_payment.tx_id)
            if tx:
                bsq_fee_per_day = self._dao_state_service.get_param_value_as_coin(
                    Param.ASSET_LISTING_FEE_PER_DAY, tx.block_height
                ).value
            else:
                bsq_fee_per_day = self._bsq_formatter.parse_param_value_to_coin(
                    Param.ASSET_LISTING_FEE_PER_DAY,
                    Param.ASSET_LISTING_FEE_PER_DAY.default_value,
                ).value
            return last_fee_payment.days_covered_by_fee(bsq_fee_per_day)
        return AssetService.DEFAULT_LOOK_BACK_PERIOD_DAYS

    def _get_fee_payments(self, stateful_asset: "StatefulAsset") -> list["FeePayment"]:
        return [
            FeePayment(tx.id, tx.burnt_fee) for tx in self._get_fee_txs(stateful_asset)
        ]

    def _get_fee_txs(self, stateful_asset: "StatefulAsset") -> list["Tx"]:
        asset_hash = AssetConsensus.get_hash(stateful_asset)
        op_return_data = AssetConsensus.get_op_return_data(asset_hash)

        return sorted(
            filter(
                lambda x: x is not None,
                (
                    self._dao_state_service.get_tx(tx_output.tx_id)
                    for tx_output in self._dao_state_service.get_asset_listing_fee_op_return_tx_outputs()
                    if tx_output.op_return_data == op_return_data
                ),
            ),
            key=lambda tx: tx.time,
        )

    def _find_asset(self, ticker_symbol: str) -> Optional["StatefulAsset"]:
        return next(
            (
                asset
                for asset in self.get_stateful_assets()
                if asset.ticker_symbol == ticker_symbol
            ),
            None,
        )

    def _was_asset_removed_by_voting(self, ticker_symbol: str) -> bool:
        is_removed = any(
            proposal.ticker_symbol == ticker_symbol
            for proposal in self._get_accepted_remove_asset_proposal_stream()
        )
        if is_removed:
            self.logger.info(
                f"Asset '{get_currency_name_and_code(ticker_symbol)}' was removed"
            )
        return is_removed

    def _get_accepted_remove_asset_proposal_stream(self):
        return (
            evaluated_proposal.proposal
            for evaluated_proposal in self._dao_state_service.get_evaluated_proposal_list()
            if isinstance(evaluated_proposal.proposal, RemoveAssetProposal)
            and evaluated_proposal.is_accepted
        )
