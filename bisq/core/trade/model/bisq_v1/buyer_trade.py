from abc import ABC 
from bisq.core.trade.model.bisq_v1.trade import Trade
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState


class BuyerTrade(Trade, ABC):
    
    def get_payout_amount(self):
        assert self.get_amount() is not None, "Invalid state: get_amount() is None at BuyerTrade.get_payout_amount()"
        assert self._offer is not None, "Invalid state: offer is None at BuyerTrade.get_payout_amount()"
        return self._offer.buyer_security_deposit.add(self.get_amount())
    
    def confirm_permitted(self):
        return not self.dispute_state_property.value.is_arbitrated
