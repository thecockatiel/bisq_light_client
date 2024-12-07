from abc import ABC 
from bisq.core.trade.model.bisq_v1.trade import Trade
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState


class SellerTrade(Trade, ABC):
    
    def get_payout_amount(self):
        assert self._offer is not None, "Invalid state: offer is None at SellerTrade.get_payout_amount()"
        return self._offer.seller_security_deposit
    
    def confirm_permitted(self):
        match self.dispute_state_property.value:
            case TradeDisputeState.NO_DISPUTE:
                return True
            
            case TradeDisputeState.DISPUTE_REQUESTED | \
                 TradeDisputeState.DISPUTE_STARTED_BY_PEER | \
                 TradeDisputeState.DISPUTE_CLOSED | \
                 TradeDisputeState.MEDIATION_REQUESTED | \
                 TradeDisputeState.MEDIATION_STARTED_BY_PEER:
                return False
                
            case TradeDisputeState.MEDIATION_CLOSED:
                return not self.mediation_result_applied_penalty_to_seller
                
            case TradeDisputeState.REFUND_REQUESTED | \
                 TradeDisputeState.REFUND_REQUEST_STARTED_BY_PEER | \
                 TradeDisputeState.REFUND_REQUEST_CLOSED | \
                 _:
                return False
