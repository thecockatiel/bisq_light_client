from datetime import datetime
from typing import TYPE_CHECKING

from bisq.common.capabilities import Capabilities
from bisq.common.config.config import Config
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.common.capability import Capability
    from bisq.core.offer.offer import Offer


class OfferRestrictions:
    # The date when the tolerated small trade amount will be changed.
    TOLERATED_SMALL_TRADE_AMOUNT_CHANGE_ACTIVATION_DATE = datetime(
        2025, 2, 17
    )
    # The date when traders who have not upgraded to a Tor v3 Node Address cannot take offers and their offers become
    # invisible.
    REQUIRE_TOR_NODE_ADDRESS_V3_DATE = datetime(2021, 8, 10)

    @staticmethod
    def requires_node_address_update():
        return (
            datetime.now()
            > OfferRestrictions.REQUIRE_TOR_NODE_ADDRESS_V3_DATE
            and not Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest()
        )

    TOLERATED_SMALL_TRADE_AMOUNT = (
        Coin.parse_coin("0.002")
        if datetime.now()
        > TOLERATED_SMALL_TRADE_AMOUNT_CHANGE_ACTIVATION_DATE
        else Coin.parse_coin("0.01")
    )

    @staticmethod
    def has_offer_mandatory_capability(
        offer: "Offer", mandatory_capability: "Capability"
    ) -> bool:
        extra_data_map = offer.extra_data_map
        if extra_data_map is not None and OfferPayload.CAPABILITIES in extra_data_map:
            comma_separated_ordinals = extra_data_map[OfferPayload.CAPABILITIES]
            capabilities = Capabilities.from_string_list(comma_separated_ordinals)
            return Capabilities.has_mandatory_capability(
                capabilities, mandatory_capability
            )
        return False
