from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.messages.payout_tx_published_message import (
    PayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


class BuyerProcessPayoutTxPublishedMessage(TradeTask):
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            if not isinstance(message, PayoutTxPublishedMessage):
                raise ValueError(
                    f"Expected PayoutTxPublishedMessage but got {message.__class__.__name__ if message else None}"
                )
            Validator.check_trade_id(self.process_model.offer_id, message)
            assert message is not None, "Message is required"
            check_argument(message.payout_tx is not None, "Payout tx is required")

            # update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            if self.trade.payout_tx is None:
                committed_payout_tx = WalletService.maybe_add_tx_to_wallet(
                    message.payout_tx,
                    self.process_model.btc_wallet_service.wallet,
                )
                self.trade.payout_tx = committed_payout_tx
                WalletService.print_tx(
                    "payoutTx received from peer", committed_payout_tx
                )

                self.trade.state_property.set(
                    TradeState.BUYER_RECEIVED_PAYOUT_TX_PUBLISHED_MSG
                )
                self.process_model.btc_wallet_service.reset_coin_locked_in_multi_sig_address_entry(
                    self.trade.get_id()
                )
            else:
                self.logger.info(
                    f"We got the payout tx already set from BuyerSetupPayoutTxListener and do nothing here. trade ID={self.trade.get_id()}"
                )

            if message.signed_witness is not None:
                # We received the signedWitness from the seller and publish the data to the network.
                # The signer has published it as well but we prefer to re-do it on our side as well to achieve higher
                # resilience.
                self.process_model.account_age_witness_service.publish_own_signed_witness(
                    message.signed_witness
                )

            self.process_model.trade_manager.request_persistence()
            self.complete()
        except Exception as e:
            self.failed(exc=e)
