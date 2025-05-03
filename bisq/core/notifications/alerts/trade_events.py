from collections.abc import Callable
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.core.locale.res import Res
from bisq.core.notifications.mobile_message import MobileMessage
from bisq.core.notifications.mobile_message_type import MobileMessageType
from bisq.core.trade.model.trade_phase import TradePhase
from utils.data import ObservableChangeEvent, SimplePropertyChangeEvent
import uuid

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.notifications.mobile_notification_service import (
        MobileNotificationService,
    )
    from bisq.core.trade.trade_manager import TradeManager


class TradeEvents:
    def __init__(
        self,
        trade_manager: "TradeManager",
        key_ring: "KeyRing",
        mobile_notification_service: "MobileNotificationService",
    ):
        self.logger = get_ctx_logger(__name__)
        self.trade_manager = trade_manager
        self.mobile_notification_service = mobile_notification_service
        self.pub_key_ring = key_ring.pub_key_ring
        self._subscriptions: list[Callable[[], None]] = []

    def on_all_services_initialized(self):
        def on_trade_changed(e: ObservableChangeEvent["Trade"]):
            if e.added_elements:
                for trade in e.added_elements:
                    self._set_trade_phase_listener(trade)

        self._subscriptions.append(
            self.trade_manager.get_observable_list().add_listener(on_trade_changed)
        )
        for trade in self.trade_manager.get_observable_list():
            self._set_trade_phase_listener(trade)

    def shut_down(self):
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

    def _set_trade_phase_listener(self, trade: "Trade"):
        self.logger.info(f"We got a new trade. id={trade.get_id()}")
        if not trade.is_payout_published:

            def on_phase_changed(e: SimplePropertyChangeEvent[TradePhase]):
                msg = None
                short_id = trade.get_short_id()

                if e.new_value in [
                    TradePhase.INIT,
                    TradePhase.TAKER_FEE_PUBLISHED,
                    TradePhase.DEPOSIT_PUBLISHED,
                ]:
                    pass

                elif e.new_value == TradePhase.DEPOSIT_CONFIRMED:
                    if (
                        trade.contract
                        and self.pub_key_ring == trade.contract.buyer_pub_key_ring
                    ):
                        msg = Res.get(
                            "account.notifications.trade.message.msg.conf", short_id
                        )

                elif e.new_value == TradePhase.FIAT_SENT:
                    # We only notify the seller
                    if (
                        trade.contract
                        and self.pub_key_ring == trade.contract.seller_pub_key_ring
                    ):
                        msg = Res.get(
                            "account.notifications.trade.message.msg.started",
                            short_id,
                        )

                elif e.new_value == TradePhase.FIAT_RECEIVED:
                    pass

                elif e.new_value == TradePhase.PAYOUT_PUBLISHED:
                    # We only notify the buyer
                    if (
                        trade.contract
                        and self.pub_key_ring == trade.contract.buyer_pub_key_ring
                    ):
                        msg = Res.get(
                            "account.notifications.trade.message.msg.completed",
                            short_id,
                        )

                elif e.new_value == TradePhase.WITHDRAWN:
                    pass

                if msg:
                    message = MobileMessage(
                        Res.get("account.notifications.trade.message.title"),
                        msg,
                        MobileMessageType.TRADE,
                        short_id,
                    )
                    try:
                        self.mobile_notification_service.send_message(message)
                    except Exception as e:
                        self.logger.error(str(e), exc_info=e)

            self._subscriptions.append(
                trade.state_phase_property.add_listener(on_phase_changed)
            )

    @staticmethod
    def get_test_messages():
        short_id = str(uuid.uuid4())[:8]
        return [
            MobileMessage(
                Res.get("account.notifications.trade.message.title"),
                Res.get("account.notifications.trade.message.msg.conf", short_id),
                MobileMessageType.TRADE,
                short_id,
            ),
            MobileMessage(
                Res.get("account.notifications.trade.message.title"),
                Res.get("account.notifications.trade.message.msg.started", short_id),
                MobileMessageType.TRADE,
                short_id,
            ),
            MobileMessage(
                Res.get("account.notifications.trade.message.title"),
                Res.get("account.notifications.trade.message.msg.completed", short_id),
                MobileMessageType.TRADE,
                short_id,
            ),
        ]
