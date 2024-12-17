from typing import TYPE_CHECKING
import uuid

from bisq.core.trade.protocol.bisq_v1.messages.peer_published_delayed_payout_tx_message import (
    PeerPublishedDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.send_mailbox_message_task import (
    SendMailboxMessageTask,
)

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import (
        TradeMailboxMessage,
    )
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade


class SendPeerPublishedDelayedPayoutTxMessage(SendMailboxMessageTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)

    def get_trade_mailbox_message(self, id: str) -> "TradeMailboxMessage":
        return PeerPublishedDelayedPayoutTxMessage(
            uid=str(uuid.uuid4()),
            trade_id=self.trade.get_id(),
            sender_node_address=self.trade.trading_peer_node_address,
        )

    def set_state_sent(self) -> None:
        pass

    def set_state_arrived(self) -> None:
        pass

    def set_state_stored_in_mailbox(self) -> None:
        pass

    def set_state_fault(self) -> None:
        pass

    def run(self) -> None:
        try:
            self.run_intercept_hook()
            super().run()
        except Exception as e:
            self.failed(exc=e)
