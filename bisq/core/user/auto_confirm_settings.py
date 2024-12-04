from abc import ABC, abstractmethod
from collections.abc import Callable
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.setup.log_setup import get_logger
from bitcoinj.base.coin import Coin
from typing import List, Optional
import proto.pb_pb2 as protobuf

from utils.concurrency import ThreadSafeSet

logger = get_logger(__name__)

class AutoConfirmSettings(PersistablePayload):
    class Listener(Callable[[], None], ABC):
        @abstractmethod
        def on_change(self):
            pass
        
        def __call__(self):
            self.on_change()

    def __init__(self, 
                 enabled: bool,
                 required_confirmations: int,
                 trade_limit: int,
                 service_addresses: List[str],
                 currency_code: str):
        self.enabled = enabled
        self.required_confirmations = required_confirmations
        self.trade_limit = trade_limit
        self.service_addresses = service_addresses
        self.currency_code = currency_code
        self.listeners = ThreadSafeSet['AutoConfirmSettings.Listener']()

    @staticmethod
    def get_default(service_addresses: List[str], currency_code: str) -> Optional['AutoConfirmSettings']:
        if currency_code == "XMR":
            return AutoConfirmSettings(
                enabled=False,
                required_confirmations=5,
                trade_limit=Coin.COIN().value,
                service_addresses=service_addresses,
                currency_code="XMR"
            )
        logger.error(f"No AutoConfirmSettings supported yet for currency {currency_code}")
        return None
    
    def to_proto_message(self):
        return protobuf.AutoConfirmSettings(
            enabled=self.enabled,
            required_confirmations=self.required_confirmations,
            trade_limit=self.trade_limit,
            service_addresses=self.service_addresses,
            currency_code=self.currency_code
        )
        
    @staticmethod
    def from_proto(proto: protobuf.AutoConfirmSettings) -> 'AutoConfirmSettings':
        return AutoConfirmSettings(
            enabled=proto.enabled,
            required_confirmations=proto.required_confirmations,
            trade_limit=proto.trade_limit,
            service_addresses=proto.service_addresses,
            currency_code=proto.currency_code,
        )

    def add_listener(self, listener: 'AutoConfirmSettings.Listener') -> None:
        self.listeners.add(listener)

    def remove_listener(self, listener: 'AutoConfirmSettings.Listener') -> None:
        self.listeners.discard(listener)

    def _notify_listeners(self) -> None:
        for listener in self.listeners:
            listener()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._notify_listeners()

    def set_required_confirmations(self, required_confirmations: int) -> None:
        self.required_confirmations = required_confirmations
        self._notify_listeners()

    def set_trade_limit(self, trade_limit: int) -> None:
        self.trade_limit = trade_limit
        self._notify_listeners()

    def set_service_addresses(self, service_addresses: List[str]) -> None:
        self.service_addresses = service_addresses
        self._notify_listeners()

    def set_currency_code(self, currency_code: str) -> None:
        self.currency_code = currency_code
        self._notify_listeners()
