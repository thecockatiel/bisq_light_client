from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, runtime_checkable

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

@runtime_checkable
class _ProtocolModelProtocol(Generic[T], Protocol):
    @abstractmethod
    def apply_transient(self, provider: 'Provider', trade_manager: "TradeManager", offer: "Offer") -> None: ...
    
    p2p_service: "P2PService" # only get needed
    
    trade_peer: T # only get needed
    
    temp_trading_peer_node_address: "NodeAddress"
    
    trade_manager: "TradeManager" # only get needed
    
    trade_message: "TradeMessage"
    
    my_node_address: "NodeAddress" # only get needed
    

class ProtocolModel(_ProtocolModelProtocol[T], TaskModel, PersistablePayload, ABC):
    pass
