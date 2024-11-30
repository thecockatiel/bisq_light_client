from datetime import datetime, timezone
from typing import TYPE_CHECKING

from bisq.common.capabilities import Capabilities
from bisq.common.config.config import CONFIG
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.common.capability import Capability
    from bisq.core.offer.offer import Offer


class OfferRestrictions:
    # The date when traders who have not upgraded to a Tor v3 Node Address cannot take offers and their offers become
    # invisible.
    REQUIRE_TOR_NODE_ADDRESS_V3_DATE = datetime(2021, 8, 10, tzinfo=timezone.utc)
    
    @staticmethod
    def requires_node_address_update():
        return datetime.now(timezone.utc) > OfferRestrictions.REQUIRE_TOR_NODE_ADDRESS_V3_DATE and not CONFIG.base_currency_network.is_regtest()
    
    TOLERATED_SMALL_TRADE_AMOUNT = Coin.parse_coin("0.01")
    
    @staticmethod
    def has_offer_mandatory_capability(offer: "Offer", mandatory_capability: "Capability") -> bool:
        extra_data_map = offer.extra_data_map
        if extra_data_map is not None and OfferPayload.CAPABILITIES in extra_data_map:
            comma_separated_ordinals = extra_data_map[OfferPayload.CAPABILITIES]
            capabilities = Capabilities.from_string_list(comma_separated_ordinals)
            return Capabilities.has_mandatory_capability(capabilities, mandatory_capability)
        return False