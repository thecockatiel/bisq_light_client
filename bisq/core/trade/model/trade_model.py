from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional, TypeVar
from bisq.common.taskrunner.task_model import TaskModel
from bisq.core.trade.model.tradable import Tradable
from utils.data import SimpleProperty
from utils.formatting import get_short_id
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.offer.offer import Offer
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.protocol.protocol_model import ProtocolModel
    from bisq.core.trade.protocol.trade_peer import TradePeer
    from bisq.core.monetary.price import Price
    from bisq.core.monetary.volume import Volume
    from bisq.core.trade.model.trade_phase import TradePhase
    from bisq.core.trade.model.trade_state import TradeState
    from bitcoinj.base.coin import Coin

_T = TypeVar("T", bound="TradePeer")

class TradeModel(Tradable, TaskModel):
    def __init__(self, uid: str, offer: "Offer", 
                 take_offer_date: Optional[int] = None,
                 trading_peer_node_address: Optional["NodeAddress"] = None,
                 error_message: Optional[str] = None):
        self._uid = uid
        self._offer = offer
        self.trading_peer_node_address = trading_peer_node_address
        self.take_offer_date = take_offer_date or get_time_ms()
        self.error_message_property = SimpleProperty[Optional[str]](error_message)

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def error_message(self) -> Optional[str]:
        return self.error_message_property.get()

    @error_message.setter
    def error_message(self, message: Optional[str]):
        self.error_message_property.set(message)

    def initialize(self, service_provider: "Provider"):
        pass

    @abstractmethod
    def is_completed(self) -> bool:
        pass

    @abstractmethod
    def get_trade_protocol_model(self) -> "ProtocolModel[_T]":
        pass

    @abstractmethod
    def get_trade_state(self) -> "TradeState":
        pass

    @abstractmethod
    def get_trade_phase(self) -> "TradePhase":
        pass

    @abstractmethod
    def get_amount_as_long(self) -> int:
        pass

    @abstractmethod
    def get_amount(self) -> "Coin":
        pass

    @abstractmethod
    def get_volume(self) -> "Volume":
        pass

    @abstractmethod
    def get_price(self) -> "Price":
        pass

    @abstractmethod
    def get_tx_fee(self) -> "Coin":
        pass

    @abstractmethod
    def get_taker_fee(self) -> "Coin":
        pass

    @abstractmethod
    def get_maker_fee(self) -> "Coin":
        pass

    def get_offer(self):
        return self._offer

    def get_date(self):
        return datetime.fromtimestamp(self.take_offer_date / 1000)

    def get_id(self) -> str:
        return self._offer.get_id()

    def get_short_id(self) -> str:
        return get_short_id(self.get_id())
