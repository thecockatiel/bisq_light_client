from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf
from typing import TYPE_CHECKING, List
from bisq.core.payment.payment_account import PaymentAccount

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver

class MarketAlertFilter(PersistablePayload):
    def __init__(self, payment_account: "PaymentAccount", trigger_value: int, is_buy_offer: bool, alert_ids: List[str] = None):
        """
        @param payment_account: The payment account used for the filter
        @param trigger_value: Percentage distance from market price (100 for 1.00%)
        @param is_buy_offer: If the offer is a buy offer
        @param alert_ids: List of offerIds for which we have sent already an alert
        """
        self.payment_account = payment_account
        self.trigger_value = trigger_value
        self.is_buy_offer = is_buy_offer
        self.alert_ids = alert_ids if alert_ids is not None else []

    def to_proto_message(self) -> protobuf.MarketAlertFilter:
        return protobuf.MarketAlertFilter(
            payment_account=self.payment_account.to_proto_message(),
            trigger_value=self.trigger_value,
            is_buy_offer=self.is_buy_offer,
            alert_ids=self.alert_ids
        )

    @staticmethod
    def from_proto(proto: protobuf.MarketAlertFilter, core_proto_resolver: "CoreProtoResolver") -> 'MarketAlertFilter':
        alert_ids = list(proto.alert_ids) if proto.alert_ids else []
        return MarketAlertFilter(
            payment_account=PaymentAccount.from_proto(proto.payment_account, core_proto_resolver),
            trigger_value=proto.trigger_value,
            is_buy_offer=proto.is_buy_offer,
            alert_ids=alert_ids
        )

    def add_alert_id(self, alert_id: str) -> None:
        if self.not_contains_alert_id(alert_id):
            self.alert_ids.append(alert_id)

    def contains_alert_id(self, alert_id: str) -> bool:
        return alert_id in self.alert_ids

    def not_contains_alert_id(self, alert_id: str) -> bool:
        return alert_id not in self.alert_ids

    def __str__(self) -> str:
        return (f"MarketAlertFilter("
                f"\n     payment_account={self.payment_account},"
                f"\n     trigger_value={self.trigger_value},"
                f"\n     is_buy_offer={self.is_buy_offer},"
                f"\n     alert_ids={self.alert_ids}"
                f"\n)")

