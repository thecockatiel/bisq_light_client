
from bisq.core.trade.model.trade_phase import TradePhase


class TradeStateProtocol:
    phase: "TradePhase"
    value: int
    name: str
    
