from typing import TYPE_CHECKING, Optional, Set, List, Dict, cast
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.notifications.alerts.market.market_alert_filter import MarketAlertFilter
from bisq.core.notifications.alerts.price.price_alert_filter import PriceAlertFilter
from bisq.core.user.cookie import Cookie
import proto.pb_pb2 as protobuf
from bisq.core.payment.payment_account import PaymentAccount
from bisq.core.alert.alert import Alert
from bisq.core.filter.filter import Filter
from bisq.core.support.dispute.arbitration.arbitrator.arbitrator import Arbitrator
from bisq.core.support.dispute.mediation.mediator.mediator import Mediator
from bisq.core.support.refund.refundagent.refund_agent import RefundAgent

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver

class UserPayload(PersistableEnvelope):
    def __init__(self,
                 account_id: Optional[str] = None,
                 payment_accounts: Optional[Set["PaymentAccount"]] = None,
                 current_payment_account: Optional["PaymentAccount"] = None,
                 accepted_language_locale_codes: Optional[List[str]] = None,
                 developers_alert: Optional["Alert"] = None,
                 displayed_alert: Optional["Alert"] = None,
                 developers_filter: Optional["Filter"] = None,
                 registered_arbitrator: Optional["Arbitrator"] = None,
                 registered_mediator: Optional["Mediator"] = None,
                 accepted_arbitrators: Optional[List["Arbitrator"]] = None,
                 accepted_mediators: Optional[List["Mediator"]] = None,
                 price_alert_filter: Optional["PriceAlertFilter"] = None,
                 market_alert_filters: Optional[List["MarketAlertFilter"]] = None,
                 registered_refund_agent: Optional["RefundAgent"] = None,
                 accepted_refund_agents: Optional[List["RefundAgent"]] = None,
                 cookie: Optional["Cookie"] = None,
                 sub_accounts_by_id: Optional[Dict[str, Set["PaymentAccount"]]] = None):
        
        self.account_id: Optional[str] = account_id
        self.payment_accounts = payment_accounts or set()
        self.current_payment_account = current_payment_account
        self.accepted_language_locale_codes = accepted_language_locale_codes or []
        self.developers_alert = developers_alert
        self.displayed_alert = displayed_alert
        self.developers_filter = developers_filter
        self.registered_arbitrator = registered_arbitrator
        self.registered_mediator = registered_mediator
        self.accepted_arbitrators = accepted_arbitrators or []
        self.accepted_mediators = accepted_mediators or []
        self.price_alert_filter = price_alert_filter
        self.market_alert_filters = market_alert_filters or []
        
        # Added v1.2.0
        self.registered_refund_agent = registered_refund_agent
        self.accepted_refund_agents = accepted_refund_agents or []
        
        # Added at v1.5.3
        # Generic map for persisting various UI states. We keep values un-typed as string to
        # provide sufficient flexibility.
        self.cookie= cookie or Cookie()
        
        # Was added at v1.9.2
        # Key is in case of XMR subAccounts the subAccountId (mainAddress + accountIndex). This creates unique sets of
        # mainAddress + accountIndex combinations.
        self.sub_accounts_by_id = sub_accounts_by_id or {}

    def to_proto_message(self) -> protobuf.PersistableEnvelope:
        payload = protobuf.UserPayload()
        
        if self.account_id:
            payload.account_id = self.account_id
            
        if self.payment_accounts:
            payload.payment_accounts.extend(ProtoUtil.collection_to_proto(self.payment_accounts, protobuf.PaymentAccount))
            
        if self.current_payment_account:
            payload.current_payment_account.CopyFrom(self.current_payment_account.to_proto_message())
            
        if self.accepted_language_locale_codes:
            payload.accepted_language_locale_codes.extend(self.accepted_language_locale_codes)
            
        if self.developers_alert:
            payload.developers_alert.CopyFrom(self.developers_alert.to_proto_message().alert)
            
        if self.displayed_alert:
            payload.displayed_alert.CopyFrom(self.displayed_alert.to_proto_message().alert)
            
        if self.developers_filter:
            payload.developers_filter.CopyFrom(self.developers_filter.to_proto_message().filter)
            
        if self.registered_arbitrator:
            payload.registered_arbitrator.CopyFrom(self.registered_arbitrator.to_proto_message().arbitrator)
            
        if self.registered_mediator:
            payload.registered_mediator.CopyFrom(self.registered_mediator.to_proto_message().mediator)
            
        if self.accepted_arbitrators:
            payload.accepted_arbitrators.extend(
                ProtoUtil.collection_to_proto_with_extra(self.accepted_arbitrators, 
                                           lambda msg: cast(protobuf.StoragePayload, msg).arbitrator))
            
        if self.accepted_mediators:
            payload.accepted_mediators.extend(
                ProtoUtil.collection_to_proto_with_extra(self.accepted_mediators,
                                           lambda msg: cast(protobuf.StoragePayload, msg).mediator))
            
        if self.price_alert_filter:
            payload.price_alert_filter.CopyFrom(self.price_alert_filter.to_proto_message())
            
        if self.market_alert_filters:
            payload.market_alert_filters.extend(
                ProtoUtil.collection_to_proto(self.market_alert_filters, protobuf.MarketAlertFilter))
            
        if self.registered_refund_agent:
            payload.registered_refund_agent.CopyFrom(self.registered_refund_agent.to_proto_message().refund_agent)
            
        if self.accepted_refund_agents:
            payload.accepted_refund_agents.extend(
                ProtoUtil.collection_to_proto_with_extra(self.accepted_refund_agents,
                                           lambda msg: cast(protobuf.StoragePayload, msg).refund_agent))
            
        if self.cookie:
            payload.cookie.update(self.cookie.to_proto_message())

        # Convert subAccountsById map to list of SubAccountMapEntry
        for key, value in self.sub_accounts_by_id.items():
            entry = protobuf.SubAccountMapEntry(
                key = key,
                value = (account.to_proto_message() for account in value)
            )
            payload.sub_account_map_entries.append(entry)

        envelope = protobuf.PersistableEnvelope()
        envelope.user_payload.CopyFrom(payload)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.UserPayload, core_proto_resolver: "CoreProtoResolver") -> "UserPayload":
        # Convert protobuf SubAccountMapEntry list to dictionary
        sub_accounts = {
            entry.key: {
                sub_account_obj
                for sub_account in entry.value
                if sub_account is not None
                if (sub_account_obj := PaymentAccount.from_proto(sub_account, core_proto_resolver)) is not None
            }
            for entry in proto.sub_account_map_entries
        }

        return UserPayload(
            account_id=ProtoUtil.string_or_none_from_proto(proto.account_id),
            payment_accounts={
                account_obj
                for account in proto.payment_accounts if account is not None
                if (account_obj := PaymentAccount.from_proto(account, core_proto_resolver)) is not None
            } if proto.payment_accounts else set(),
            current_payment_account=PaymentAccount.from_proto(proto.current_payment_account, core_proto_resolver) 
                if proto.HasField("current_payment_account") else None,
            accepted_language_locale_codes=list(proto.accepted_language_locale_codes) if proto.accepted_language_locale_codes else [],
            developers_alert=Alert.from_proto(proto.developers_alert) if proto.HasField("developers_alert") else None,
            displayed_alert=Alert.from_proto(proto.displayed_alert) if proto.HasField("displayed_alert") else None,
            developers_filter=Filter.from_proto(proto.developers_filter) if proto.HasField("developers_filter") else None,
            registered_arbitrator=Arbitrator.from_proto(proto.registered_arbitrator) if proto.HasField("registered_arbitrator") else None,
            registered_mediator=Mediator.from_proto(proto.registered_mediator) if proto.HasField("registered_mediator") else None,
            accepted_arbitrators=[
                Arbitrator.from_proto(arbitrator)
                for arbitrator in proto.accepted_arbitrators
            ] if proto.accepted_arbitrators else [],
            accepted_mediators=[
                Mediator.from_proto(mediator)
                for mediator in proto.accepted_mediators
            ] if proto.accepted_mediators else [],
            price_alert_filter=PriceAlertFilter.from_proto(proto.price_alert_filter),
            market_alert_filters=[
                MarketAlertFilter.from_proto(filter, core_proto_resolver)
                for filter in proto.market_alert_filters
            ] if proto.market_alert_filters else [],
            registered_refund_agent=RefundAgent.from_proto(proto.registered_refund_agent) if proto.HasField("registered_refund_agent") else None,
            accepted_refund_agents=[
                RefundAgent.from_proto(agent)
                for agent in proto.accepted_refund_agents
            ] if proto.accepted_refund_agents else [],
            cookie=Cookie.from_proto(proto.cookie),
            sub_accounts_by_id=sub_accounts
        )

