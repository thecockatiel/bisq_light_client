from typing import TYPE_CHECKING, Optional
from bisq.common.taskrunner.task_model import TaskModel

if TYPE_CHECKING:
    from bisq.core.user.user import User
    from bisq.core.support.dispute.mediation.mediator.mediator_manager import MediatorManager
    from bisq.core.offer.availability.messages.offer_availability_response import OfferAvailabilityResponse
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.offer import Offer
    from bisq.common.crypto.pub_key_ring import PubKeyRing

# TODO: implement TradeStatisticsManager and DelayedPayoutTxReceiverService if necessary
# But its omitted for now.

class OfferAvailabilityModel(TaskModel):
    def __init__(
        self,
        offer: 'Offer',
        pub_key_ring: 'PubKeyRing',
        p2p_service: 'P2PService',
        user: 'User',
        mediator_manager: 'MediatorManager',
        # trade_statistics_manager: 'TradeStatisticsManager'
        # delayed_payout_tx_receiver_service: 'DelayedPayoutTxReceiverService',
        is_taker_api_user: bool
    ):
        super().__init__()
        self.offer = offer
        self.pub_key_ring = pub_key_ring # takers PubKey (my pubkey)
        self.p2p_service = p2p_service
        self.user = user
        self.mediator_manager = mediator_manager
        # Added in v 1.9.7
        # self.delayed_payout_tx_receiver_service = delayed_payout_tx_receiver_service
        # Added in v1.5.5
        self.is_taker_api_user = is_taker_api_user
        
        self.peer_node_address: Optional['NodeAddress'] = None # maker 
        self.message: Optional['OfferAvailabilityResponse'] = None
        self.selected_arbitrator: Optional['NodeAddress'] = None
        # Added in v1.1.6
        self.selected_mediator: Optional['NodeAddress'] = None
        # Added in v1.2.0
        self.selected_refund_agent: Optional['NodeAddress'] = None

    
    def get_takers_trade_price(self) -> int:
        return self.offer.get_price().value if self.offer.get_price() is not None else 0
    
    def on_complete(self):
        pass
