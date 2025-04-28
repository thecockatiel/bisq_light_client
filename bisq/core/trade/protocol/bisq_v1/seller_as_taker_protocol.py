from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.model.bisq_v1.seller_as_taker_trade import SellerAsTakerTrade
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_response import (
    InputsForDepositTxResponse,
)
from bisq.core.trade.protocol.bisq_v1.seller_protocol import SellerProtocol
from bisq.core.trade.protocol.bisq_v1.taker_protocol import TakerProtocol
from bisq.core.trade.protocol.bisq_v1.taker_protocol_event import TakerProtocolEvent
from bisq.core.trade.protocol.bisq_v1.tasks.apply_filter import ApplyFilter
from bisq.core.trade.protocol.bisq_v1.tasks.check_if_dao_state_is_in_sync import (
    CheckIfDaoStateIsInSync,
)
from bisq.core.trade.protocol.bisq_v1.tasks.check_restrictions import CheckRestrictions
from bisq.core.trade.protocol.bisq_v1.tasks.seller.maybe_create_sub_account import (
    MaybeCreateSubAccount,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_creates_delayed_payout_tx import (
    SellerCreatesDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_send_delayed_payout_tx_signature_request import (
    SellerSendDelayedPayoutTxSignatureRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller.seller_signs_delayed_payout_tx import (
    SellerSignsDelayedPayoutTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller_as_taker.seller_as_taker_creates_deposit_tx_inputs import (
    SellerAsTakerCreatesDepositTxInputs,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller_as_taker.seller_as_taker_signs_deposit_tx import (
    SellerAsTakerSignsDepositTx,
)
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
from bisq.core.trade.protocol.trade_message import TradeMessage
from utils.preconditions import check_not_none




class SellerAsTakerProtocol(SellerProtocol, TakerProtocol):

    def __init__(self, trade: "SellerAsTakerTrade"):
        super().__init__(trade)
        self.logger = get_ctx_logger(__name__)
        offer = check_not_none(trade.get_offer())
        self.process_model.trade_peer.pub_key_ring = offer.pub_key_ring

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // User interaction: Take offer
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_take_offer(self):
        self.expect(
            self.add_phase(TradePhase.INIT)
            .with_event(TakerProtocolEvent.TAKE_OFFER)
            .from_peer(self.trade.trading_peer_node_address)
        ).with_setup(
            self.with_tasks(
                CheckIfDaoStateIsInSync,
                MaybeCreateSubAccount,
                ApplyFilter,
                CheckRestrictions,
                self.get_verify_peers_fee_payment_class(),
                CreateTakerFeeTx,
                SellerAsTakerCreatesDepositTxInputs,
                TakerSendInputsForDepositTxRequest,
            ).with_timeout(120)
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
                SellerAsTakerSignsDepositTx,
                SellerCreatesDelayedPayoutTx,
                SellerSignsDelayedPayoutTx,
                SellerSendDelayedPayoutTxSignatureRequest,
            ).with_timeout(120)
        ).execute_tasks()

    # We keep the handler here in as well to make it more transparent which messages we expect

    def handle_delayed_payout_tx_signature_request(self, message, peer):
        return super().handle_delayed_payout_tx_signature_request(message, peer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming message when buyer has clicked payment started button
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We keep the handler here in as well to make it more transparent which messages we expect
    def handle_counter_currency_transfer_started_message(self, message, peer):
        return super().handle_counter_currency_transfer_started_message(message, peer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // User interaction
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We keep the handler here in as well to make it more transparent which events we expect
    def on_payment_received(
        self,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        return super().on_payment_received(result_handler, error_message_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Massage dispatcher
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_trade_message(self, message: "TradeMessage", peer: "NodeAddress"):
        super().on_trade_message(message, peer)

        self.logger.info(
            f"Received {message.__class__.__name__} from {peer} with tradeId {message.trade_id} and uid {message.uid}"
        )

        if isinstance(message, InputsForDepositTxResponse):
            self._handle_inputs_for_deposit_tx_response(message, peer)

    def get_verify_peers_fee_payment_class(self):
        return TakerVerifyMakerFeePayment
