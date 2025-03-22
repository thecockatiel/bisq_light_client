from typing import TYPE_CHECKING
from bisq.common.handlers.result_handler import ResultHandler
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.protocol.bisq_v1.buyer_protocol import BuyerProtocol
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_response import InputsForDepositTxResponse
from bisq.core.trade.protocol.bisq_v1.messages.payout_tx_published_message import (
    PayoutTxPublishedMessage,
)
from bisq.core.trade.protocol.bisq_v1.taker_protocol import TakerProtocol
from bisq.core.trade.protocol.bisq_v1.taker_protocol_event import TakerProtocolEvent
from bisq.core.trade.protocol.bisq_v1.tasks.apply_filter import ApplyFilter
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_finalizes_delayed_payout_tx import (
    BuyerFinalizesDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_process_delayed_payout_tx_signature_request import (
    BuyerProcessDelayedPayoutTxSignatureRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_sends_delayed_payout_tx_signature_response import (
    BuyerSendsDelayedPayoutTxSignatureResponse,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_setup_deposit_tx_listener import (
    BuyerSetupDepositTxListener,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_signs_delayed_payout_tx import (
    BuyerSignsDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer.buyer_verifies_prepared_delayed_payout_tx import (
    BuyerVerifiesPreparedDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer_as_taker.buyer_as_taker_creates_deposit_tx_inputs import (
    BuyerAsTakerCreatesDepositTxInputs,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer_as_taker.buyer_as_taker_sends_deposit_tx_message import (
    BuyerAsTakerSendsDepositTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer_as_taker.buyer_as_taker_signs_deposit_tx import (
    BuyerAsTakerSignsDepositTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.check_if_dao_state_is_in_sync import (
    CheckIfDaoStateIsInSync,
)
from bisq.core.trade.protocol.bisq_v1.tasks.check_restrictions import CheckRestrictions

from bisq.core.trade.protocol.bisq_v1.tasks.taker.create_taker_fee_tx import (
    CreateTakerFeeTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.taker.taker_processes_inputs_for_deposit_tx_response import (
    TakerProcessesInputsForDepositTxResponse,
)
from bisq.core.trade.protocol.bisq_v1.tasks.taker.taker_publish_fee_tx import (
    TakerPublishFeeTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.taker.taker_send_inputs_for_deposit_tx_request import (
    TakerSendInputsForDepositTxRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.taker.taker_verify_and_sign_contract import (
    TakerVerifyAndSignContract,
)
from bisq.core.trade.protocol.bisq_v1.tasks.taker.taker_verify_taker_fee_payment import (
    TakerVerifyMakerFeePayment,
)
from utils.preconditions import check_not_none
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import (
    InputsForDepositTxRequest,
)

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import (
        DepositTxAndDelayedPayoutTxMessage,
    )
    from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_request import (
        DelayedPayoutTxSignatureRequest,
    )
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.network.p2p.node_address import NodeAddress

    from bisq.core.trade.model.bisq_v1.buyer_as_taker_trade import BuyerAsTakerTrade


class BuyerAsTakerProtocol(BuyerProtocol, TakerProtocol):

    def __init__(self, trade: "BuyerAsTakerTrade"):
        super().__init__(trade)

        offer = check_not_none(trade.get_offer())
        self.process_model.trade_peer.pub_key_ring = offer.pub_key_ring

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Take offer
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_take_offer(self):
        self.expect(
            self.add_phase(TradePhase.INIT).with_event(TakerProtocolEvent.TAKE_OFFER)
        ).with_setup(
            self.with_tasks(
                CheckIfDaoStateIsInSync,
                ApplyFilter,
                CheckRestrictions,
                self.get_verify_peers_fee_payment_class(),
                CreateTakerFeeTx,
                BuyerAsTakerCreatesDepositTxInputs,
                TakerSendInputsForDepositTxRequest,
            ).with_timeout(120)
        ).run(
            lambda: (
                setattr(
                    self.process_model,
                    "temp_trading_peer_node_address",
                    self.trade.trading_peer_node_address,
                ),
                self.process_model.trade_manager.request_persistence(),
            )
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming messages Take offer process
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _handle_inputs_for_deposit_tx_response(
        self, message: "InputsForDepositTxResponse", peer: "NodeAddress"
    ):
        self.expect(
            self.add_phase(TradePhase.INIT).with_message(message).from_peer(peer)
        ).with_setup(
            self.with_tasks(
                TakerProcessesInputsForDepositTxResponse,
                ApplyFilter,
                TakerVerifyAndSignContract,
                TakerPublishFeeTx,
                BuyerAsTakerSignsDepositTx,
                BuyerSetupDepositTxListener,
                BuyerAsTakerSendsDepositTxMessage,
            ).with_timeout(120)
        ).execute_tasks()

    def handle_delayed_payout_tx_signature_request(
        self, message: "DelayedPayoutTxSignatureRequest", peer: "NodeAddress"
    ):
        self.expect(
            self.add_phase(TradePhase.TAKER_FEE_PUBLISHED)
            .with_message(message)
            .from_peer(peer)
        ).with_setup(
            self.with_tasks(
                BuyerProcessDelayedPayoutTxSignatureRequest,
                BuyerVerifiesPreparedDelayedPayoutTx,
                BuyerSignsDelayedPayoutTx,
                BuyerFinalizesDelayedPayoutTx,
                BuyerSendsDelayedPayoutTxSignatureResponse,
            ).with_timeout(120)
        ).execute_tasks()

    # We keep the handler here in as well to make it more transparent which messages we expect
    def handle_deposit_tx_and_delayed_payout_tx_message(
        self, message: "DepositTxAndDelayedPayoutTxMessage", peer: "NodeAddress"
    ):
        return super().handle_deposit_tx_and_delayed_payout_tx_message(message, peer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // User interaction
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We keep the handler here in as well to make it more transparent which events we expect
    def on_payment_started(
        self,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        return super().on_payment_started(result_handler, error_message_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming message Payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We keep the handler here in as well to make it more transparent which messages we expect
    def handle_payout_tx_published_message(
        self, message: "PayoutTxPublishedMessage", peer: "NodeAddress"
    ):
        return super().handle_payout_tx_published_message(message, peer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message dispatcher
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_trade_message(self, message, peer: "NodeAddress"):
        super().on_trade_message(message, peer)

        if isinstance(message, InputsForDepositTxResponse):
            self._handle_inputs_for_deposit_tx_response(message, peer)

    def get_verify_peers_fee_payment_class(self):
        return TakerVerifyMakerFeePayment
