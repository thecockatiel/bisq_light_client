from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.message_state import MessageState
from bisq.core.trade.protocol.bisq_v1.messages.share_buyer_payment_account_message import (
    ShareBuyerPaymentAccountMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.send_mailbox_message_task import (
    SendMailboxMessageTask,
)
from utils.data import SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.common.timer import Timer
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade

logger = get_logger(__name__)


class BuyerSendsShareBuyerPaymentAccountMessage(SendMailboxMessageTask):
    MAX_RESEND_ATTEMPTS = 7

    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)
        self.delay_in_sec = 4
        self.resend_counter = 0
        self.message: Optional["ShareBuyerPaymentAccountMessage"] = None
        self.listener: Optional[
            Callable[[SimplePropertyChangeEvent["MessageState"]], None]
        ] = None
        self.timer: Optional["Timer"] = None

    def get_trade_mailbox_message(
        self, trade_id: str
    ) -> "ShareBuyerPaymentAccountMessage":
        if self.message is None:
            deterministic_id = (
                trade_id + self.process_model.my_node_address.get_full_address()
            )
            buyer_payment_account_payload = (
                self.process_model.get_payment_account_payload(self.trade)
            )
            self.message = ShareBuyerPaymentAccountMessage(
                uid=deterministic_id,
                trade_id=self.process_model.offer_id,
                sender_node_address=self.process_model.my_node_address,
                buyer_payment_account_payload=buyer_payment_account_payload,
            )
        return self.message

    def set_state_sent(self) -> None:
        pass

    def set_state_arrived(self) -> None:
        self._cleanup()
        # Complete is called in base class

    # We override the default behaviour for onStoredInMailbox and do not call complete
    def on_stored_in_mailbox(self) -> None:
        self.set_state_stored_in_mailbox()

    def set_state_stored_in_mailbox(self) -> None:
        if not self.trade.is_deposit_confirmed:
            self._try_to_send_again_later()

    # We override the default behaviour for onFault and do not call appendToErrorMessage and failed
    def on_fault(self, error_message: str, message: "TradeMessage") -> None:
        self.set_state_fault()

    def set_state_fault(self) -> None:
        if not self.trade.is_deposit_confirmed:
            self._try_to_send_again_later()

    def run(self) -> None:
        try:
            self.run_intercept_hook()
            super().run()
        except Exception as e:
            self.failed(exc=e)
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        if self.timer is not None:
            self.timer.stop()
        if self.listener is not None:
            self.process_model.deposit_tx_message_state_property.remove_listener(
                self.listener
            )

    def _try_to_send_again_later(self) -> None:
        if (
            self.resend_counter
            >= BuyerSendsShareBuyerPaymentAccountMessage.MAX_RESEND_ATTEMPTS
        ):
            self._cleanup()
            self.failed(
                f"We never received an ACK message when sending the msg to the peer. "
                f"We fail here and do not publish the deposit tx."
            )
            return

        logger.info(
            f"We send the message again to the peer after a delay of {self.delay_in_sec} sec."
        )
        if self.timer is not None:
            self.timer.stop()
        self.timer = UserThread.run_after(
            self.run, timedelta(seconds=self.delay_in_sec)
        )

        if self.resend_counter == 0:
            # We want to register listener only once
            self.listener = lambda e: self._on_message_state_change(e.new_value)
            self.process_model.deposit_tx_message_state_property.add_listener(
                self.listener
            )
            self._on_message_state_change(
                self.process_model.deposit_tx_message_state_property.get()
            )

        self.delay_in_sec *= 2
        self.resend_counter += 1

    def _on_message_state_change(self, new_value: MessageState) -> None:
        # Once we receive an ACK from our msg we know the peer has received the msg and we stop
        if new_value == MessageState.ACKNOWLEDGED:
            self.process_model.trade_manager.request_persistence()
            self._cleanup()
            self.complete()
