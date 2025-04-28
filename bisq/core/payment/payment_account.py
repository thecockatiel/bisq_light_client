from dataclasses import dataclass, field 
from typing import TYPE_CHECKING, Optional
from abc import ABC, abstractmethod
import uuid
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.setup.log_setup import get_ctx_logger
import pb_pb2 as protobuf
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.common.protocol.proto_util import ProtoUtil
from utils.time import get_time_ms
from datetime import datetime


if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_method import PaymentMethod
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver


@dataclass
class PaymentAccount(PersistablePayload, ABC):
    payment_method: 'PaymentMethod'
    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)
    creation_date: int = field(default_factory=get_time_ms, init=False)
    payment_account_payload: 'PaymentAccountPayload' = field(default=None)
    account_name: str = field(default=None)
    persisted_account_name: str = field(default=None, compare=False)
    
    trade_currencies: list['TradeCurrency'] = field(default_factory=list)
    selected_trade_currency: Optional['TradeCurrency'] = field(default=None)
    
    # Was added at v1.9.2
    extra_data: Optional[dict[str, str]] = field(default=None)

    def __post_init__(self):
        self.init()
        
    def __hash__(self):
        return hash((self.payment_method, self.id, self.creation_date, self.account_name))
        
    def init(self):
        self.payment_account_payload = self.create_payload() 

    def to_proto_message(self) -> 'protobuf.PaymentAccount':
        assert self.account_name is not None, "account_name must not be null"
        builder = protobuf.PaymentAccount(
            payment_method=self.payment_method.to_proto_message(),
            id=self.id,
            creation_date=self.creation_date,
            payment_account_payload=self.payment_account_payload.to_proto_message(),
            account_name=self.account_name,
            trade_currencies=ProtoUtil.collection_to_proto(self.trade_currencies, protobuf.TradeCurrency)
        )
        
        if self.selected_trade_currency:
            builder.selected_trade_currency.CopyFrom(self.selected_trade_currency.to_proto_message())
        
        if self.extra_data:
            builder.extra_data.extend(ProtoUtil.to_string_map_entry_list(self.extra_data))
            
        return builder

    @staticmethod
    def from_proto(proto: 'protobuf.PaymentAccount', core_proto_resolver: "CoreProtoResolver") -> Optional['PaymentAccount']:
        from bisq.core.payment.payload.payment_method import PaymentMethod
        
        payment_method_id = proto.payment_method.id
        trade_currencies = [TradeCurrency.from_proto(tc) for tc in proto.trade_currencies]

        # Remove NGN for Transferwise
        ngn_tw = next((curr for curr in trade_currencies 
                      if payment_method_id == PaymentMethod.TRANSFERWISE_ID and curr.code == "NGN"), None)
        if ngn_tw:
            try:
                trade_currencies.remove(ngn_tw)
            except:
                pass

        from bisq.core.payment.payment_account_factory import PaymentAccountFactory
        try:
            account = PaymentAccountFactory.get_payment_account(PaymentMethod.get_payment_method(payment_method_id))
            account.trade_currencies.clear()
            account.id = proto.id
            account.creation_date = proto.creation_date
            account.account_name = proto.account_name
            account.persisted_account_name = proto.account_name
            account.trade_currencies.extend(trade_currencies)
            account.payment_account_payload = core_proto_resolver.from_proto(proto.payment_account_payload)

            if proto.HasField('selected_trade_currency'):
                account.selected_trade_currency = TradeCurrency.from_proto(proto.selected_trade_currency)

            account.extra_data = ProtoUtil.to_string_map(proto.extra_data)
            
            return account
            
        except Exception as e:
            logger = get_ctx_logger(__name__)
            logger.warning(f"Could not load account: {payment_method_id}, exception: {str(e)}")
            return None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_creation_date(self) -> datetime:
        return datetime.fromtimestamp(self.creation_date / 1000)

    def add_currency(self, trade_currency: 'TradeCurrency') -> None:
        if trade_currency not in self.trade_currencies:
            self.trade_currencies.append(trade_currency)

    def remove_currency(self, trade_currency: 'TradeCurrency') -> None:
        try:
            self.trade_currencies.remove(trade_currency)
        except:
            pass

    @property
    def has_multiple_currencies(self) -> bool:
        return len(self.trade_currencies) > 1

    def set_single_trade_currency(self, trade_currency: 'TradeCurrency') -> None:
        self.trade_currencies.clear()
        self.trade_currencies.append(trade_currency)
        self.selected_trade_currency = trade_currency

    def get_single_trade_currency(self) -> Optional['TradeCurrency']:
        return self.trade_currencies[0] if len(self.trade_currencies) == 1 else None

    def get_max_trade_period(self) -> int:
        return self.payment_method.max_trade_period

    @abstractmethod
    def create_payload(self) -> 'PaymentAccountPayload':
        pass

    @property
    def salt(self) -> bytes:
        return self.payment_account_payload.salt

    @salt.setter
    def salt(self, salt: bytes) -> None:
        self.payment_account_payload.salt = salt
        
    @property
    def salt_as_hex(self) -> str: 
        return self.salt.hex()
    
    @salt_as_hex.setter
    def salt_as_hex(self, salt_as_hex: str) -> None: 
        self.salt = bytes.fromhex(salt_as_hex)

    @property
    def holder_name(self) -> str:
        return self.payment_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str) -> None:
        self.payment_account_payload.holder_name = value

    @property
    def owner_id(self) -> str:
        return self.payment_account_payload.owner_id

    @property
    def is_country_based_payment_account(self) -> bool:
        return False
    
    def has_payment_method_with_id(self, payment_method_id: str):
        return self.payment_method.id == payment_method_id
    
    def get_trade_currency(self) -> Optional["TradeCurrency"]:
        """
        Return an Optional of the trade currency for this payment account, or none if not found.  
        If this payment account has a selected trade currency, that is returned,
        else its single trade currency is returned,
        else the first trade currency in this payment account's tradeCurrencies list is returned.
        """
        if self.selected_trade_currency is not None:
            return self.selected_trade_currency
        elif self.get_single_trade_currency() is not None:
            return self.get_single_trade_currency()
        elif self.trade_currencies:
            return self.trade_currencies[0]
        return None
        
    def on_add_to_user(self):
        # We are in the process to get added to the user. This is called just before saving the account and the
        # last moment we could apply some special handling if needed (e.g. as it happens for Revolut)
        pass
        
    def get_pre_trade_message(self, is_buyer: bool) -> Optional[str]:
        if is_buyer:
            return self.get_message_for_buyer()
        else:
            return self.get_message_for_seller()
            
    # will be overridden by specific account when necessary
    def get_message_for_buyer(self) -> Optional[str]:
        return None
        
    # will be overridden by specific account when necessary
    def get_message_for_seller(self) -> Optional[str]:
        return None
        
    # will be overridden by specific account when necessary
    def get_message_for_account_creation(self) -> Optional[str]:
        return None
        
    def on_persist_changes(self) -> None:
        self.persisted_account_name = self.account_name
        
    def revert_changes(self) -> None:
        self.account_name = self.persisted_account_name
        
    @abstractmethod
    def get_supported_currencies(self) -> list['TradeCurrency']:
        pass
        
    def get_or_create_extra_data(self) -> dict[str, str]:
        if self.extra_data is None:
            self.extra_data = {}
        return self.extra_data

