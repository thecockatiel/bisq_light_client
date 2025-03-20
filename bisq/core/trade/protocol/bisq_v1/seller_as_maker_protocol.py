from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.model.bisq_v1.seller_as_maker_trade import SellerAsMakerTrade
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.protocol.bisq_v1.maker_protocol import MakerProtocol
from bisq.core.trade.protocol.bisq_v1.messages.deposit_tx_message import (
    DepositTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import (
    InputsForDepositTxRequest,
)
from bisq.core.trade.protocol.bisq_v1.seller_protocol import SellerProtocol
from bisq.core.trade.protocol.bisq_v1.tasks.apply_filter import ApplyFilter
from bisq.core.trade.protocol.bisq_v1.tasks.check_if_dao_state_is_in_sync import (
    CheckIfDaoStateIsInSync,
)
from bisq.core.trade.protocol.bisq_v1.tasks.check_restrictions import CheckRestrictions
from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_create_and_sign_contract import (
    MakerCreateAndSignContract,
)
from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_processes_inputs_for_deposit_tx_request import (
    MakerProcessesInputsForDepositTxRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_removes_open_offer import (
    MakerRemovesOpenOffer,
)
from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_sets_lock_time import (
    MakerSetsLockTime,
)
from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_verify_taker_fee_payment import (
    MakerVerifyTakerFeePayment,
)
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
from bisq.core.trade.protocol.bisq_v1.tasks.seller_as_maker.seller_as_maker_creates_unsigned_deposit_tx import (
    SellerAsMakerCreatesUnsignedDepositTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller_as_maker.seller_as_maker_finalizes_deposit_tx import (
    SellerAsMakerFinalizesDepositTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller_as_maker.seller_as_maker_process_deposit_tx_message import (
    SellerAsMakerProcessDepositTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.seller_as_maker.seller_as_maker_sends_inputs_for_deposit_tx_response import (
    SellerAsMakerSendsInputsForDepositTxResponse,
)
from bisq.core.trade.protocol.trade_message import TradeMessage
from bisq.core.trade.protocol.trade_task_runner import TradeTaskRunner

logger = get_logger(__name__)


class SellerAsMakerProtocol(SellerProtocol, MakerProtocol):
    def __init__(self, trade: "SellerAsMakerTrade"):
        super().__init__(trade)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Handle take offer request
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_take_offer_request(
        self,
        message: "InputsForDepositTxRequest",
        peer: "NodeAddress",
        error_message_handler: "ErrorMessageHandler",
    ):
        self.expect(
            self.add_phase(TradePhase.INIT).with_message(message).from_peer(peer)
        ).with_setup(
            self.with_tasks(
                CheckIfDaoStateIsInSync,
                MaybeCreateSubAccount,
                MakerProcessesInputsForDepositTxRequest,
                ApplyFilter,
                CheckRestrictions,
                self.get_verify_peers_fee_payment_class(),
                MakerSetsLockTime,
                MakerCreateAndSignContract,
                SellerAsMakerCreatesUnsignedDepositTx,
                SellerAsMakerSendsInputsForDepositTxResponse,
            )
            .using(
                TradeTaskRunner(
                    self.trade,
                    lambda: self.handle_task_runner_success(message),
                    lambda error_message: (
                        error_message_handler(error_message),
                        self.handle_task_runner_fault(
                            message=message, error_message=error_message
                        ),
                    ),
                )
            )
            .with_timeout(120)
        ).execute_tasks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming messages Take offer process
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_deposit_tx_message(
        self,
        message: "DepositTxMessage",
        peer: "NodeAddress",
    ):
        self.expect(
            self.add_phase(TradePhase.TAKER_FEE_PUBLISHED)
            .with_message(message)
            .from_peer(peer)
        ).with_setup(
            self.with_tasks(
                MakerRemovesOpenOffer,
                SellerAsMakerProcessDepositTxMessage,
                SellerAsMakerFinalizesDepositTx,
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
    def on_payment_received(self, result_handler, error_message_handler):
        return super().on_payment_received(result_handler, error_message_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Massage dispatcher
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_trade_message(self, message: "TradeMessage", peer: "NodeAddress"):
        super().on_trade_message(message, peer)

        logger.info(
            f"Received {message.__class__.__name__} from {peer} with tradeId "
            f"{message.trade_id} and uid {message.uid}"
        )

        if isinstance(message, DepositTxMessage):
            self.handle_deposit_tx_message(message, peer)

    def get_verify_peers_fee_payment_class(self):
        return MakerVerifyTakerFeePayment
