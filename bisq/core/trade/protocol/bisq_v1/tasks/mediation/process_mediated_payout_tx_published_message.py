from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.support.dispute.mediation.mediation_result_state import (
    MediationResultState,
)
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_published_message import (
    MediatedPayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

logger = get_logger(__name__)


class ProcessMediatedPayoutTxPublishedMessage(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)

    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            if not isinstance(message, MediatedPayoutTxPublishedMessage):
                raise ValueError(
                    f"Invalid message type. expected type: MediatedPayoutTxPublishedMessage, actual type: {type(message)}"
                )
            Validator.check_trade_id(self.process_model.offer_id, message)
            check_argument(message.payout_tx is not None, "message.payout_tx must not be None")

            # update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            if self.trade.get_payout_tx() is None:
                committed_mediated_payout_tx = (
                    WalletService.maybe_add_network_tx_to_wallet(
                        message.payout_tx,
                        self.process_model.btc_wallet_service.wallet,
                    )
                )
                self.trade.set_payout_tx(committed_mediated_payout_tx)
                logger.info(
                    f"MediatedPayoutTx received from peer. Txid: {committed_mediated_payout_tx.get_tx_id()}\nhex: {committed_mediated_payout_tx.bitcoin_serialize().hex()}"
                )

                self.trade.mediation_result_state = (
                    MediationResultState.RECEIVED_PAYOUT_TX_PUBLISHED_MSG
                )

                if self.trade.get_payout_tx() is not None:
                    # We need to delay that call as we might get executed at startup after mailbox messages are
                    # applied where we iterate over out pending trades. The close_disputed_trade method would remove
                    # that trade from the list causing a ConcurrentModificationException.
                    # To avoid that we delay for one render frame.
                    UserThread.execute(
                        lambda: self.process_model.trade_manager.close_disputed_trade(
                            self.trade.get_id(), TradeDisputeState.MEDIATION_CLOSED
                        )
                    )

                self.process_model.btc_wallet_service.reset_coin_locked_in_multi_sig_address_entry(
                    self.trade.get_id()
                )
            else:
                logger.info(
                    f"We got the payout tx already set from BuyerSetupPayoutTxListener and do nothing here. trade ID={self.trade.get_id()}",
                )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
