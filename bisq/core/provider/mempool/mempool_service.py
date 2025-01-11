from asyncio import Future
from typing import TYPE_CHECKING

from bisq.core.provider.mempool.mempool_request import MempoolRequest


if TYPE_CHECKING:
    from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
    from bisq.core.dao.burningman.burning_man_presentation_service import BurningManPresentationService
    from bisq.common.config.config import Config
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.user.preferences import Preferences

# TODO
class MempoolService:
    def __init__(self,
                 socks5_proxy_provider: 'Socks5ProxyProvider',
                 config: 'Config',
                 preferences: 'Preferences',
                 filter_manager: 'FilterManager',
                 dao_facade: 'DaoFacade',
                 dao_state_service: 'DaoStateService',
                 burning_man_presentation_service: 'BurningManPresentationService'):
        self.socks5_proxy_provider = socks5_proxy_provider
        self.config = config
        self.preferences = preferences
        self.filter_manager = filter_manager
        self.dao_facade = dao_facade
        self.dao_state_service = dao_state_service
        self.burning_man_presentation_service = burning_man_presentation_service
        self.outstanding_requests = 0

    def on_all_services_initialized(self):
        pass
    
    def request_tx_as_hex(self, tx_id: str) -> Future[str]:
        self.outstanding_requests += 1
        request = MempoolRequest(self.preferences, self.socks5_proxy_provider).request_tx_as_hex(tx_id)
        def on_done(_):
            self.outstanding_requests -= 1
        request.add_done_callback(on_done)
        return request
    
    def can_request_be_made(self, offer_payload: "OfferPayload" = None) -> bool:
        can = self.dao_state_service.parse_block_chain_complete and self.outstanding_requests < 5 # limit max simultaneous lookups
        if offer_payload:
            #  when validating a new offer, wait 1 block for the tx to propagate
            can = can and offer_payload.block_height_at_offer_creation < self.dao_state_service.get_chain_height()
        return can
