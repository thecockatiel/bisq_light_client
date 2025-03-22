from typing import TYPE_CHECKING
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_logger
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.protocol.bisq_v1.dispute_protocol_event import DisputeProtocolEvent
from bisq.core.trade.protocol.bisq_v1.messages.counter_currency_transfer_started_message import (
    CounterCurrencyTransferStartedMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import (
    DepositTxAndDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_signature_message import (
    MediatedPayoutTxSignatureMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.peer_published_delayed_payout_tx_message import (
    PeerPublishedDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.apply_filter import ApplyFilter
from bisq.core.trade.protocol.bisq_v1.tasks.arbitration.published_delayed_payout_tx import (
    PublishedDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.arbitration.send_peer_published_delayed_payout_tx_message import (
    SendPeerPublishedDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.broadcast_mediated_payout_tx import (
    BroadcastMediatedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.finalize_mediated_payout_tx import (
    FinalizeMediatedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.process_mediated_payout_signature_message import (
    ProcessMediatedPayoutSignatureMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.process_mediated_payout_tx_published_message import (
    ProcessMediatedPayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.send_mediated_payout_signature_message import (
    SendMediatedPayoutSignatureMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.send_mediated_payout_tx_published_message import (
    SendMediatedPayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.setup_mediated_payout_tx_listener import (
    SetupMediatedPayoutTxListener,
)
from bisq.core.trade.protocol.bisq_v1.tasks.mediation.sign_mediated_payout_tx import (
    SignMediatedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.process_peer_published_delayed_payout_tx_message import (
    ProcessPeerPublishedDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.trade_protocol import TradeProtocol
from bisq.core.trade.protocol.trade_task_runner import TradeTaskRunner
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_published_message import (
    MediatedPayoutTxPublishedMessage,
)

if TYPE_CHECKING:
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.core.network.p2p.ack_message import AckMessage
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.model.bisq_v1.trade import Trade

logger = get_logger(__name__)


class DisputeProtocol(TradeProtocol):
    def __init__(self, trade: "Trade"):
        super().__init__(trade)
        self.trade = trade
        self.process_model = trade.process_model

    def on_initialized(self):
        super().on_initialized()
        self.process_model.apply_payment_account(self.trade)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TradeProtocol implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_ack_message(self, ack_message: "AckMessage", peer: "NodeAddress"):
        # We handle the ack for CounterCurrencyTransferStartedMessage and DepositTxAndDelayedPayoutTxMessage
        # as we support automatic re-send of the msg in case it was not ACKed after a certain time
        if (
            ack_message.source_msg_class_name
            == CounterCurrencyTransferStartedMessage.__class__.__name__
        ):
            self.process_model.set_payment_started_ack_message(ack_message)
        elif (
            ack_message.source_msg_class_name
            == DepositTxAndDelayedPayoutTxMessage.__class__.__name__
        ):
            self.process_model.set_deposit_tx_sent_ack_message(ack_message)

        if ack_message.success:
            logger.info(
                f"Received AckMessage for {ack_message.source_msg_class_name} from {peer} "
                f"with tradeId {self.trade_model.get_id()} and uid {ack_message.source_uid}"
            )
        else:
            logger.warning(
                f"Received AckMessage with error state for {ack_message.source_msg_class_name} "
                f"from {peer} with tradeId {self.trade_model.get_id()} and "
                f"errorMessage={ack_message.error_message}"
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // User interaction: Trader accepts mediation result
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Trader has not yet received the peer's signature but has clicked the accept button.
    def on_accept_mediation_result(
        self,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        event = DisputeProtocolEvent.MEDIATION_RESULT_ACCEPTED

        self.expect(
            self.add_phases(
                TradePhase.DEPOSIT_CONFIRMED,
                TradePhase.FIAT_SENT,
                TradePhase.FIAT_RECEIVED,
            )
            .with_event(event)
            .with_precondition(
                (self.trade.process_model.trade_peer.mediated_payout_tx_signature 
                 is None) or (self.trade.payout_tx is None),
                lambda: error_message_handler(
                    "We either have received already the signature from the peer or Payout tx is already published."
                ),
            )
        ).with_setup(
            self.with_tasks(
                ApplyFilter,
                SignMediatedPayoutTx,
                SendMediatedPayoutSignatureMessage,
                SetupMediatedPayoutTxListener,
            ).using(
                TradeTaskRunner(
                    self.trade,
                    lambda: [result_handler(), self.handle_task_runner_success(event)],
                    lambda error_msg: [
                        error_message_handler(error_msg),
                        self.handle_task_runner_fault(
                            message=event, error_message=error_msg
                        ),
                    ],
                )
            )
        ).execute_tasks()

    # Trader has already received the peer's signature and has clicked the accept button as well.
    def on_finalize_mediation_result_payout(
        self,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        event = DisputeProtocolEvent.MEDIATION_RESULT_ACCEPTED

        self.expect(
            self.add_phases(
                TradePhase.DEPOSIT_CONFIRMED,
                TradePhase.FIAT_SENT,
                TradePhase.FIAT_RECEIVED,
            )
            .with_event(event)
            .with_precondition(
                self.trade.payout_tx is None,
                lambda: error_message_handler("Payout tx is already published."),
            )
        ).with_setup(
            self.with_tasks(
                ApplyFilter,
                SignMediatedPayoutTx,
                FinalizeMediatedPayoutTx,
                BroadcastMediatedPayoutTx,
                SendMediatedPayoutTxPublishedMessage,
            ).using(
                TradeTaskRunner(
                    self.trade,
                    lambda: [result_handler(), self.handle_task_runner_success(event)],
                    lambda error_msg: [
                        error_message_handler(error_msg),
                        self.handle_task_runner_fault(
                            message=event, error_message=error_msg
                        ),
                    ],
                )
            )
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Mediation: incoming message
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_mediated_payout_tx_signature_message(
        self, message: "MediatedPayoutTxSignatureMessage", peer: "NodeAddress"
    ) -> None:
        self.expect(
            self.add_phases(
                TradePhase.DEPOSIT_CONFIRMED,
                TradePhase.FIAT_SENT,
                TradePhase.FIAT_RECEIVED,
            )
            .with_message(message)
            .from_peer(peer)
        ).with_setup(self.with_tasks(ProcessMediatedPayoutSignatureMessage)).execute_tasks()

    def handle_mediated_payout_tx_published_message(
        self, message: "MediatedPayoutTxPublishedMessage", peer: "NodeAddress"
    ) -> None:
        self.expect(
            self.add_phases(
                TradePhase.DEPOSIT_CONFIRMED,
                TradePhase.FIAT_SENT,
                TradePhase.FIAT_RECEIVED,
            )
            .with_message(message)
            .from_peer(peer)
        ).with_setup(
            self.with_tasks(ProcessMediatedPayoutTxPublishedMessage)
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delayed payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_publish_delayed_payout_tx(
        self,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        event = DisputeProtocolEvent.ARBITRATION_REQUESTED

        self.expect(
            self.add_phases(
                TradePhase.DEPOSIT_CONFIRMED,
                TradePhase.FIAT_SENT,
                TradePhase.FIAT_RECEIVED,
            )
            .with_event(event)
            .with_precondition(
                self.trade.delayed_payout_tx is not None,
                lambda: error_message_handler("Delayed payout tx is null"),
            )
        ).with_setup(
            self.with_tasks(
                PublishedDelayedPayoutTx,
                SendPeerPublishedDelayedPayoutTxMessage,
            ).using(
                TradeTaskRunner(
                    self.trade,
                    lambda: [result_handler(), self.handle_task_runner_success(event)],
                    lambda error_msg: [
                        error_message_handler(error_msg),
                        self.handle_task_runner_fault(
                            message=event, error_message=error_msg
                        ),
                    ],
                )
            )
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Peer has published the delayed payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_peer_published_delayed_payout_tx_message(
        self, message: "PeerPublishedDelayedPayoutTxMessage", peer: "NodeAddress"
    ) -> None:
        self.expect(
            self.add_phases(
                TradePhase.DEPOSIT_CONFIRMED,
                TradePhase.FIAT_SENT,
                TradePhase.FIAT_RECEIVED,
            )
            .with_message(message)
            .from_peer(peer)
        ).with_setup(
            self.with_tasks(ProcessPeerPublishedDelayedPayoutTxMessage)
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Dispatcher
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_trade_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        if isinstance(message, MediatedPayoutTxSignatureMessage):
            self.handle_mediated_payout_tx_signature_message(message, peer)
        elif isinstance(message, MediatedPayoutTxPublishedMessage):
            self.handle_mediated_payout_tx_published_message(message, peer)
        elif isinstance(message, PeerPublishedDelayedPayoutTxMessage):
            self.handle_peer_published_delayed_payout_tx_message(message, peer)

    def on_mailbox_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        super().on_mailbox_message(message, peer)
        if isinstance(message, MediatedPayoutTxSignatureMessage):
            self.handle_mediated_payout_tx_signature_message(message, peer)
        elif isinstance(message, MediatedPayoutTxPublishedMessage):
            self.handle_mediated_payout_tx_published_message(message, peer)
        elif isinstance(message, PeerPublishedDelayedPayoutTxMessage):
            self.handle_peer_published_delayed_payout_tx_message(message, peer)
