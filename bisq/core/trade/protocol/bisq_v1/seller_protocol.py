from abc import abstractmethod
from typing import TYPE_CHECKING
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_logger
from bisq.core.trade.model.bisq_v1.seller_trade import SellerTrade
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.dispute_protocol import DisputeProtocol
from bisq.core.trade.protocol.bisq_v1.messages.counter_currency_transfer_started_message import (
    CounterCurrencyTransferStartedMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_response import (
    DelayedPayoutTxSignatureResponse,
)
from bisq.core.trade.protocol.bisq_v1.messages.share_buyer_payment_account_message import (
    ShareBuyerPaymentAccountMessage,
)
from bisq.core.trade.protocol.bisq_v1.seller_event import SellerEvent
from bisq.core.trade.protocol.bisq_v1.tasks.apply_filter import ApplyFilter
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_broadcast_payout_tx import SellerBroadcastPayoutTx
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_finalizes_delayed_payout_tx import SellerFinalizesDelayedPayoutTx
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_process_counter_currency_transfer_started_message import SellerProcessCounterCurrencyTransferStartedMessage
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_process_delayed_payout_tx_signature_response import SellerProcessDelayedPayoutTxSignatureResponse
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_process_share_buyer_payment_account_message import SellerProcessShareBuyerPaymentAccountMessage
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_publishes_deposit_tx import SellerPublishesDepositTx
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_publishes_trade_statistics import SellerPublishesTradeStatistics
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_send_payout_tx_published_message import SellerSendPayoutTxPublishedMessage
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_sends_deposit_tx_and_delayed_payout_tx_message import SellerSendsDepositTxAndDelayedPayoutTxMessage
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_sign_and_finalize_payout_tx import SellerSignAndFinalizePayoutTx
from bisq.core.trade.protocol.bisq_v1.tasks.verify_peers_account_age_witness import VerifyPeersAccountAgeWitness
from bisq.core.trade.protocol.trade_task_runner import TradeTaskRunner

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.protocol.trade_message import TradeMessage

logger = get_logger(__name__)

class SellerProtocol(DisputeProtocol):

    def __init__(self, trade: "SellerTrade"):
        super().__init__(trade)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Mailbox
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_mailbox_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        super().on_mailbox_message(message, peer)

        if isinstance(message, CounterCurrencyTransferStartedMessage):
            self.handle(message, peer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming messages
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle(self, message: "TradeMessage", peer: "NodeAddress") -> None:

        if isinstance(message, DelayedPayoutTxSignatureResponse):
            self.expect(
                self.add_phase(TradePhase.TAKER_FEE_PUBLISHED)
                .with_message(message)
                .from_peer(peer)
            ).with_setup(
                self.with_tasks(
                    SellerProcessDelayedPayoutTxSignatureResponse,
                    SellerFinalizesDelayedPayoutTx,
                    SellerSendsDepositTxAndDelayedPayoutTxMessage,
                    SellerPublishesDepositTx,
                    SellerPublishesTradeStatistics,
                )
            ).execute_tasks()
        elif isinstance(message, ShareBuyerPaymentAccountMessage):
            self.expect(
                self.add_phases(
                    TradePhase.TAKER_FEE_PUBLISHED,
                    TradePhase.DEPOSIT_PUBLISHED,
                    TradePhase.DEPOSIT_CONFIRMED,
                )
                .with_message(message)
                .from_peer(peer)
            ).with_setup(
                self.with_tasks(
                    SellerProcessShareBuyerPaymentAccountMessage,
                    ApplyFilter,
                    VerifyPeersAccountAgeWitness,
                )
            ).run(
                # We stop timeout here and don't start a new one as the
                # SellerSendsDepositTxAndDelayedPayoutTxMessage repeats to send the message and has it's own
                # timeout if it never succeeds.
                self.stop_timeout
            ).execute_tasks()
        elif isinstance(message, CounterCurrencyTransferStartedMessage):
            # We are more tolerant with expected phase and allow also DEPOSIT_PUBLISHED as it can be the case
            # that the wallet is still syncing and so the DEPOSIT_CONFIRMED state to yet triggered when we received
            # a mailbox message with CounterCurrencyTransferStartedMessage.
            # JAVA TODO A better fix would be to add a listener for the wallet sync state and process
            # the mailbox msg once wallet is ready and trade state set.
            self.expect(
                self.add_phases(
                    TradePhase.DEPOSIT_CONFIRMED,
                    TradePhase.DEPOSIT_PUBLISHED,
                )
                .with_message(message)
                .from_peer(peer)
                .with_precondition(
                    self.trade.get_payout_tx() is None,
                    lambda: (
                        logger.warning(
                            "We received a CounterCurrencyTransferStartedMessage but we have already created the payout tx "
                            "so we ignore the message. This can happen if the ACK message to the peer did not "
                            "arrive and the peer repeats sending us the message. We send another ACK msg."
                        ),
                        self.send_ack_message(message, True, None),
                        self.remove_mailbox_message_after_processing(message),
                    ),
                )
            ).with_setup(
                self.with_tasks(
                    SellerProcessCounterCurrencyTransferStartedMessage,
                    ApplyFilter,
                    self.get_verify_peers_fee_payment_class(),
                )
            ).execute_tasks()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // User interaction
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_payment_received(self, result_handler: ResultHandler, error_message_handler: ErrorMessageHandler) -> None:
        event = SellerEvent.PAYMENT_RECEIVED
        self.expect(
            self.add_phases(
                TradePhase.FIAT_SENT,
                TradePhase.PAYOUT_PUBLISHED,
            )
            .with_event(event)
            .with_precondition(self.trade.confirm_permitted())
        ).with_setup(
            self.with_tasks(
                ApplyFilter,
                self.get_verify_peers_fee_payment_class(),
                SellerSignAndFinalizePayoutTx,
                SellerBroadcastPayoutTx,
                SellerSendPayoutTxPublishedMessage,
            ).using(
                TradeTaskRunner(
                    self.trade,
                    lambda: (
                        result_handler(),
                        self.handle_task_runner_success(event),
                    ),
                    lambda error_message: (
                        error_message_handler(error_message),
                        self.handle_task_runner_fault(event, error_message),
                    ),
                )
            )
        ).run(
            lambda: (
                self.trade.state_property.set(TradeState.SELLER_CONFIRMED_IN_UI_FIAT_PAYMENT_RECEIPT),
                self.process_model.trade_manager.request_persistence(),
            )
        ).execute_tasks()
        
    
    def on_trade_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        logger.info(
            f"Received {message.__class__.__name__} from {peer} with tradeId {message.trade_id} and uid {message.uid}"
        )

        super().on_trade_message(message, peer)

        self.handle(message, peer)
        
    @abstractmethod
    def get_verify_peers_fee_payment_class(self) -> "TradeTask":
        pass
