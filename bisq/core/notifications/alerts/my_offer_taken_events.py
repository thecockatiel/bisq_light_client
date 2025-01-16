from typing import TYPE_CHECKING
import uuid

from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from bisq.core.notifications.mobile_message import MobileMessage
from bisq.core.notifications.mobile_message_type import MobileMessageType
from bisq.core.offer.open_offer_state import OpenOfferState
from utils.data import ObservableChangeEvent


if TYPE_CHECKING:
    from bisq.core.offer.open_offer import OpenOffer
    from bisq.core.notifications.mobile_notification_service import (
        MobileNotificationService,
    )
    from bisq.core.offer.open_offer_manager import OpenOfferManager

logger = get_logger(__name__)


class MyOfferTakenEvents:

    def __init__(
        self,
        mobile_notification_service: "MobileNotificationService",
        open_offer_manager: "OpenOfferManager",
    ):
        self.mobile_notification_service = mobile_notification_service
        self.open_offer_manager = open_offer_manager

    def on_all_services_initialized(self):
        def on_offer_changed(e: ObservableChangeEvent["OpenOffer"]):
            if e.removed_elements:
                for offer in e.removed_elements:
                    self._on_open_offer_removed(offer)

        self.open_offer_manager.get_observable_list().add_listener(on_offer_changed)
        for offer in self.open_offer_manager.get_observable_list():
            self._on_open_offer_removed(offer)

    def _on_open_offer_removed(self, open_offer: "OpenOffer"):
        state = open_offer.state
        if state == OpenOfferState.RESERVED:
            logger.info(
                f"We got a offer removed. id={open_offer.get_id()}, state={state.name}"
            )
            short_id = open_offer.get_short_id()
            message = MobileMessage(
                Res.get("account.notifications.offer.message.title"),
                Res.get("account.notifications.offer.message.msg", short_id),
                MobileMessageType.OFFER,
                short_id,
            )
            try:
                self.mobile_notification_service.send_message(message)
            except Exception as e:
                logger.error(str(e), exc_info=e)

    @staticmethod
    def get_test_msg():
        short_id = str(uuid.uuid4())[:8]
        return MobileMessage(
            Res.get("account.notifications.offer.message.title"),
            Res.get("account.notifications.offer.message.msg", short_id),
            MobileMessageType.OFFER,
            short_id,
        )
