from typing import TYPE_CHECKING
from bisq.common.handlers.result_handler import ResultHandler
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.protocol.bisq_v1.buyer_protocol import BuyerProtocol
from bisq.core.trade.protocol.bisq_v1.maker_protocol import MakerProtocol
from bisq.core.trade.protocol.bisq_v1.messages.payout_tx_published_message import (
    PayoutTxPublishedMessage,
)
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
from bisq.core.trade.protocol.bisq_v1.tasks.buyer_as_maker.buyer_as_maker_creates_and_signs_deposit_tx import (
    BuyerAsMakerCreatesAndSignsDepositTx,
)
from bisq.core.trade.protocol.bisq_v1.tasks.buyer_as_maker.buyer_as_maker_sends_inputs_for_deposit_tx_response import (
    BuyerAsMakerSendsInputsForDepositTxResponse,
)
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
from bisq.core.trade.protocol.trade_task_runner import TradeTaskRunner

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import (
        DepositTxAndDelayedPayoutTxMessage,
    )
    from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_request import (
        DelayedPayoutTxSignatureRequest,
    )
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import (
        InputsForDepositTxRequest,
    )
    from bisq.core.trade.model.bisq_v1.buyer_as_maker_trade import BuyerAsMakerTrade


class BuyerAsMakerProtocol(BuyerProtocol, MakerProtocol):

    def __init__(self, trade: "BuyerAsMakerTrade"):
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
                MakerProcessesInputsForDepositTxRequest,
                ApplyFilter,
                CheckRestrictions,
                self.get_verify_peers_fee_payment_class(),
                MakerSetsLockTime,
                MakerCreateAndSignContract,
                BuyerAsMakerCreatesAndSignsDepositTx,
                BuyerSetupDepositTxListener,
                BuyerAsMakerSendsInputsForDepositTxResponse,
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

    def handle_delayed_payout_tx_signature_request(
        self,
        message: "DelayedPayoutTxSignatureRequest",
        peer: "NodeAddress",
    ):
        self.expect(
            self.add_phase(TradePhase.TAKER_FEE_PUBLISHED)
            .with_message(message)
            .from_peer(peer)
        ).with_setup(
            self.with_tasks(
                MakerRemovesOpenOffer,
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

    def get_verify_peers_fee_payment_class(self):
        return MakerVerifyTakerFeePayment
