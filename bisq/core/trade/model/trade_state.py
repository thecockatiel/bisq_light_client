from abc import ABC, abstractmethod
from enum import Enum

from bisq.core.trade.model.trade_phase import TradePhase

class TradeState(ABC):
    def get_trade_phase(self) -> "TradePhase.Phase":
        return TradePhase.Phase.DEFAULT
    
    @abstractmethod
    def ordinal(self) -> int:
        pass
    
    @abstractmethod
    def name(self) -> str:
        pass
