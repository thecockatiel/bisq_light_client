from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.taskrunner.task_model import TaskModel
from bisq.core.trade.protocol.trade_peer import TradePeer
from bisq.core.trade.trade_manager import TradeManager 

if TYPE_CHECKING:
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.protocol.trade_message import TradeMessage

T = TypeVar('T', bound=TradePeer)

class ProtocolModel(Generic[T], TaskModel, PersistablePayload, ABC):
    @abstractmethod
    def apply_transient(self, provider: 'Provider', trade_manager: "TradeManager", offer: "Offer") -> None:
        pass

    @abstractmethod
    def get_p2p_service(self) -> "P2PService":
        pass

    @abstractmethod
    def get_trade_peer(self) -> T:
        pass

    @abstractmethod
    def set_temp_trading_peer_node_address(self, node_address: "NodeAddress") -> None:
        pass

    @abstractmethod
    def get_temp_trading_peer_node_address(self) -> "NodeAddress":
        pass

    @abstractmethod
    def get_trade_manager(self) -> "TradeManager":
        pass

    @abstractmethod
    def set_trade_message(self, trade_message: "TradeMessage") -> None:
        pass

    @abstractmethod
    def get_my_node_address(self) -> "NodeAddress":
        pass

