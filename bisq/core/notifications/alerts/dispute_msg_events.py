from typing import TYPE_CHECKING
import uuid

from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from bisq.core.notifications.mobile_message import MobileMessage
from bisq.core.notifications.mobile_message_type import MobileMessageType
from utils.data import ObservableChangeEvent


if TYPE_CHECKING:
    from bisq.core.support.messages.chat_messsage import ChatMessage
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.notifications.mobile_notification_service import (
        MobileNotificationService,
    )
    from bisq.core.support.dispute.mediation.mediation_manager import MediationManager
    from bisq.core.support.refund.refund_manager import RefundManager

logger = get_logger(__name__)


class DisputeMsgEvents:

    def __init__(
        self,
        refund_manager: "RefundManager",
        mediation_manager: "MediationManager",
        p2p_service: "P2PService",
        mobile_notification_service: "MobileNotificationService",
    ):
        self.refund_manager = refund_manager
        self.mediation_manager = mediation_manager
        self.p2p_service = p2p_service
        self.mobile_notification_service = mobile_notification_service

    def on_all_services_initialized(self):
        def on_dispute_changed(e: ObservableChangeEvent["Dispute"]):
            if e.added_elements:
                for dispute in e.added_elements:
                    self._set_dispute_listener(dispute)

        self.refund_manager.get_disputes_as_observable_list().add_listener(
            on_dispute_changed
        )
        for dispute in self.mediation_manager.get_disputes_as_observable_list():
            self._set_dispute_listener(dispute)

        self.mediation_manager.get_disputes_as_observable_list().add_listener(
            on_dispute_changed
        )
        for dispute in self.mediation_manager.get_disputes_as_observable_list():
            self._set_dispute_listener(dispute)

        # We do not need a handling for unread messages as mailbox messages arrive later and will trigger the
        # event listeners. But the existing messages are not causing a notification.

    @staticmethod
    def get_test_msg():
        short_id = str(uuid.uuid4())[:8]
        return MobileMessage(
            Res.get("account.notifications.dispute.message.title"),
            Res.get("account.notifications.dispute.message.msg", short_id),
            MobileMessageType.DISPUTE,
            short_id,
        )

    def _set_dispute_listener(self, dispute: "Dispute"):
        logger.debug(
            f"We got a dispute added. id={dispute.id}, tradeId={dispute.trade_id}"
        )

        def on_chat_messages_changed(e: ObservableChangeEvent["ChatMessage"]):
            if e.added_elements:
                logger.debug(
                    f"We got a ChatMessage added. id={dispute.id}, tradeId={dispute.trade_id}"
                )
                for chat_message in e.added_elements:
                    self._on_chat_message(chat_message)

        dispute.chat_messages.add_listener(on_chat_messages_changed)

    def _on_chat_message(self, chat_message: "ChatMessage"):
        if chat_message.sender_node_address == self.p2p_service.address:
            return

        # We only send msg in case we are not the sender
        short_id = chat_message.get_short_id()
        message = MobileMessage(
            Res.get("account.notifications.dispute.message.title"),
            Res.get("account.notifications.dispute.message.msg", short_id),
            MobileMessageType.DISPUTE,
            short_id,
        )
        try:
            self.mobile_notification_service.send_message(message)
        except Exception as e:
            logger.error(str(e), exc_info=e)
