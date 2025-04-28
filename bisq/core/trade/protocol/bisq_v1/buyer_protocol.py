from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.buyer_event import BuyerEvent
from bisq.core.trade.protocol.bisq_v1.dispute_protocol import DisputeProtocol
from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import (
    DepositTxAndDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.payout_tx_published_message import (
    PayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_request import (
    DelayedPayoutTxSignatureRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.apply_filter import ApplyFilter
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_process_deposit_tx_and_delayed_payout_tx_message import (
    BuyerProcessDepositTxAndDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_process_payout_tx_published_message import (
    BuyerProcessPayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_send_counter_currency_transfer_started_message import (
    BuyerSendCounterCurrencyTransferStartedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_sends_share_buyer_payment_account_message import (
    BuyerSendsShareBuyerPaymentAccountMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_setup_deposit_tx_listener import (
    BuyerSetupDepositTxListener,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_setup_payout_tx_listener import (
    BuyerSetupPayoutTxListener,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_sign_payout_tx import (
    BuyerSignPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_verifies_final_delayed_payout_tx import (
    BuyerVerifiesFinalDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.verify_peers_account_age_witness import (
    VerifyPeersAccountAgeWitness,
)
from bisq.core.trade.protocol.trade_task_runner import TradeTaskRunner

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.core.trade.model.bisq_v1.buyer_trade import BuyerTrade


class BuyerProtocol(DisputeProtocol, ABC):

    def __init__(self, trade: "BuyerTrade"):
        super().__init__(trade)
        self.logger = get_ctx_logger(__name__)

    def on_initialized(self):
        super().on_initialized()
        # We get called the constructor with any possible state and phase. As we don't want to log an error for such
        # cases we use the alternative 'given' method instead of 'expect'.
        self.given(
            self.add_phase(TradePhase.TAKER_FEE_PUBLISHED).with_event(
                BuyerEvent.STARTUP
            )
        ).with_setup(self.with_tasks(BuyerSetupDepositTxListener)).execute_tasks()

        self.given(
            self.add_phases(TradePhase.FIAT_SENT, TradePhase.FIAT_RECEIVED).with_event(
                BuyerEvent.STARTUP
            )
        ).with_setup(self.with_tasks(BuyerSetupPayoutTxListener)).execute_tasks()

        self.given(
            self.add_phases(TradePhase.FIAT_SENT, TradePhase.FIAT_RECEIVED)
            .add_states(
                TradeState.BUYER_STORED_IN_MAILBOX_FIAT_PAYMENT_INITIATED_MSG,
                TradeState.BUYER_SEND_FAILED_FIAT_PAYMENT_INITIATED_MSG,
            )
            .with_event(BuyerEvent.STARTUP)
        ).with_setup(
            self.with_tasks(BuyerSendCounterCurrencyTransferStartedMessage)
        ).execute_tasks()

    def on_mailbox_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        super().on_mailbox_message(message, peer)

        if isinstance(message, DepositTxAndDelayedPayoutTxMessage):
            self.handle_deposit_tx_and_delayed_payout_tx_message(message, peer)
        elif isinstance(message, PayoutTxPublishedMessage):
            self.handle_payout_tx_published_message(message, peer)

    @abstractmethod
    def handle_delayed_payout_tx_signature_request(
        self, message: "DelayedPayoutTxSignatureRequest", peer: "NodeAddress"
    ):
        pass

    # The DepositTxAndDelayedPayoutTxMessage is a mailbox message. Earlier we used only the deposit tx which can
    # be set also when received by the network once published by the peer so that message was not mandatory and could
    # have arrived as mailbox message.
    # Now we send the delayed payout tx as well and with that this message is mandatory for continuing the protocol.
    # We do not support mailbox message handling during the take offer process as it is expected that both peers
    # are online.
    # For backward compatibility and extra resilience we still keep DepositTxAndDelayedPayoutTxMessage as a
    # mailbox message but the stored in mailbox case is not expected and the seller would try to send the message again
    # in the hope to reach the buyer directly in case of network issues.
    def handle_deposit_tx_and_delayed_payout_tx_message(
        self, message: "DepositTxAndDelayedPayoutTxMessage", peer: "NodeAddress"
    ):
        self.expect(
            self.add_phases(
                TradePhase.TAKER_FEE_PUBLISHED, TradePhase.DEPOSIT_PUBLISHED
            )
            .with_message(message)
            .from_peer(peer)
            .with_precondition(
                self.trade.deposit_tx is None
                or self.trade.process_model.trade_peer.payment_account_payload is None,
                lambda: (
                    self.logger.warning(
                        "We received a DepositTxAndDelayedPayoutTxMessage but we have already processed the deposit and "
                        "delayed payout tx so we ignore the message. This can happen if the ACK message to the peer did not "
                        "arrive and the peer repeats sending us the message. We send another ACK msg."
                    ),
                    self.stop_timeout(),
                    self.send_ack_message(message, True, None),
                    self.remove_mailbox_message_after_processing(message),
                ),
            )
        ).with_setup(
            self.with_tasks(
                BuyerProcessDepositTxAndDelayedPayoutTxMessage,
                ApplyFilter,
                VerifyPeersAccountAgeWitness,
                BuyerSendsShareBuyerPaymentAccountMessage,
                BuyerVerifiesFinalDelayedPayoutTx,
            ).using(
                TradeTaskRunner(
                    self.trade,
                    lambda: (
                        self.stop_timeout(),
                        self.handle_task_runner_success(message),
                    ),
                    lambda error_message: self.handle_task_runner_fault(
                        message=message, error_message=error_message
                    ),
                )
            )
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // User interaction
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_payment_started(
        self,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        event = BuyerEvent.PAYMENT_SENT
        self.expect(
            self.add_phase(TradePhase.DEPOSIT_CONFIRMED)
            .with_event(event)
            .with_precondition(self.trade.confirm_permitted())
        ).with_setup(
            self.with_tasks(
                ApplyFilter,
                self.get_verify_peers_fee_payment_class(),
                BuyerSignPayoutTx,
                BuyerSetupPayoutTxListener,
                BuyerSendCounterCurrencyTransferStartedMessage,
            ).using(
                TradeTaskRunner(
                    self.trade,
                    lambda: (
                        result_handler.handle_result(),
                        self.handle_task_runner_success(event),
                    ),
                    lambda error_message: (
                        error_message_handler(error_message),
                        self.handle_task_runner_fault(
                            message=event, error_message=error_message
                        ),
                    ),
                )
            )
        ).run(
            lambda: (
                self.trade.state_property.set(
                    TradeState.BUYER_CONFIRMED_IN_UI_FIAT_PAYMENT_INITIATED
                ),
                self.trade.process_model.trade_manager.request_persistence(),
            )
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming message Payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_payout_tx_published_message(
        self, message: "PayoutTxPublishedMessage", peer: "NodeAddress"
    ):
        self.expect(
            self.add_phases(TradePhase.FIAT_SENT, TradePhase.PAYOUT_PUBLISHED)
            .with_message(message)
            .from_peer(peer)
        ).with_setup(
            self.with_tasks(BuyerProcessPayoutTxPublishedMessage)
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message dispatcher
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_trade_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        super().on_trade_message(message, peer)

        self.logger.info(
            f"Received {message.__class__.__name__} from {peer} with tradeId {message.trade_id} and uid {message.uid}"
        )

        if isinstance(message, DelayedPayoutTxSignatureRequest):
            self.handle_delayed_payout_tx_signature_request(message, peer)
        elif isinstance(message, DepositTxAndDelayedPayoutTxMessage):
            self.handle_deposit_tx_and_delayed_payout_tx_message(message, peer)
        elif isinstance(message, PayoutTxPublishedMessage):
            self.handle_payout_tx_published_message(message, peer)

    @abstractmethod
    def get_verify_peers_fee_payment_class(self) -> "TradeTask":
        pass
