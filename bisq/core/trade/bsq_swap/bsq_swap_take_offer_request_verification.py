from typing import TYPE_CHECKING
from datetime import timedelta
from math import abs

from bisq.common.setup.log_setup import get_logger
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.util.coin.coin_util import CoinUtil
from bisq.core.util.validator import Validator
from bitcoinj.base.coin import Coin
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.trade.protocol.bsq_swap.messages.bsq_swap_request import BsqSwapRequest

logger = get_logger(__name__)

class BsqSwapTakeOfferRequestVerification:
    MINUTES_10_IN_MILLIS = int(timedelta(minutes=10).total_seconds()*1000)
    
    @staticmethod
    def is_valid(open_offer_manager: 'OpenOfferManager',
                 fee_service: 'FeeService',
                 key_ring: 'KeyRing',
                 peer: 'NodeAddress',
                 request: 'BsqSwapRequest') -> bool:
        try:
            logger.info(f"Received {request.__class__.__name__} from {peer} with tradeId {request.trade_id} and uid {request.uid}")
            
            assert request is not None, "Request cannot be None"
            assert Validator.non_empty_string_of(request.trade_id), "Trade ID must be valid"
            
            assert request.sender_node_address == peer, "Node address not matching"
            
            open_offer = open_offer_manager.get_open_offer_by_id(request.trade_id)
            assert open_offer is not None, "Offer not found in open offers"
            
            assert open_offer.state == OpenOfferState.AVAILABLE, "Offer not available"
            
            offer = open_offer.offer
            Validator.check_trade_id(offer.id, request)
            assert offer.is_my_offer(key_ring), "Offer must be mine"
            
            trade_amount = request.trade_amount
            amount_as_coin = Coin.value_of(request.trade_amount)
            
            assert (trade_amount >= offer.min_amount.value and 
                   trade_amount <= offer.amount.value), "TradeAmount not within offers amount range"
            assert BsqSwapTakeOfferRequestVerification._is_date_in_tolerance(request), "Trade date is out of tolerance"
            assert BsqSwapTakeOfferRequestVerification._is_tx_fee_in_tolerance(request, fee_service), "Miner fee from taker not in tolerance"
            
            maker_fee = CoinUtil.get_maker_fee(False, amount_as_coin)
            taker_fee = CoinUtil.get_taker_fee(False, amount_as_coin)
            assert maker_fee is not None and request.maker_fee == maker_fee.value
            assert taker_fee is not None and request.taker_fee == taker_fee.value
            
            return True

        except Exception as e:
            logger.error(f"BsqSwapTakeOfferRequestVerification failed. Request={request}, peer={peer}, error={str(e)}")
            return False

    @staticmethod
    def _is_date_in_tolerance(request: 'BsqSwapRequest') -> bool:
        return abs(request.trade_date - get_time_ms()) < BsqSwapTakeOfferRequestVerification.MINUTES_10_IN_MILLIS

    @staticmethod
    def _is_tx_fee_in_tolerance(request: 'BsqSwapRequest', fee_service: 'FeeService') -> bool:
        my_fee = fee_service.get_tx_fee_per_vbyte().value
        peers_fee = Coin.value_of(request.tx_fee_per_vbyte).value
        
        # Allow for 50% diff in mining fee, ie, maker will accept taker fee that's less
        # than 50% off their own fee from service (that is, 100% higher or 50% lower).
        # Both parties will use the same fee while creating the bsq swap tx.
        diff = abs(1 - my_fee / peers_fee)
        is_in_tolerance = diff < 0.5
        
        if not is_in_tolerance:
            logger.warning(f"Miner fee from taker not in tolerance. myFee={my_fee}, peersFee={peers_fee}, diff={diff}")
        
        return is_in_tolerance
