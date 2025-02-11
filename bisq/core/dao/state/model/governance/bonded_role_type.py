from enum import Enum

from bisq.common.config.config import Config
from bisq.core.locale.res import Res


class BondedRoleType(Enum):
    """
    Data here must not be changed as it would break backward compatibility! In case we need to change we need to add a
    new entry and maintain the old one. Once all the role holders of an old deprecated role have revoked the
    role might get removed.

    Add entry to translation file "dao.bond.bondedRoleType...."

    Name of the BondedRoleType must not change as that is used for serialisation in Protobuffer. The data fields are not part of
    the PB serialisation so changes for those would not change the hash for the dao state hash chain.
    As the data is not used in consensus critical code yet changing fields can be tolerated.
    For mediators and arbitrators we will use automated verification of the bond so there might be issues when we change
    the values. So let's avoid changing anything here beside adding new entries.
    """

    UNDEFINED = (0, 0, "N/A", False)
    # admins
    GITHUB_ADMIN = (50, 110, "https://bisq.network/roles/16", True)
    FORUM_ADMIN = (20, 110, "https://bisq.network/roles/19", True)
    TWITTER_ADMIN = (20, 110, "https://bisq.network/roles/21", True)
    ROCKET_CHAT_ADMIN = (20, 110, "https://bisq.network/roles/79", True)
    YOUTUBE_ADMIN = (10, 110, "https://bisq.network/roles/56", True)

    # maintainers
    BISQ_MAINTAINER = (50, 110, "https://bisq.network/roles/63", True)
    BITCOINJ_MAINTAINER = (20, 110, "https://bisq.network/roles/8", True)
    NETLAYER_MAINTAINER = (20, 110, "https://bisq.network/roles/81", True)

    # operators
    WEBSITE_OPERATOR = (50, 110, "https://bisq.network/roles/12", True)
    FORUM_OPERATOR = (50, 110, "https://bisq.network/roles/19", True)
    SEED_NODE_OPERATOR = (20, 110, "https://bisq.network/roles/15", True)
    DATA_RELAY_NODE_OPERATOR = (20, 110, "https://bisq.network/roles/14", True)
    BTC_NODE_OPERATOR = (5, 110, "https://bisq.network/roles/67", True)
    MARKETS_OPERATOR = (20, 110, "https://bisq.network/roles/9", True)
    BSQ_EXPLORER_OPERATOR = (20, 110, "https://bisq.network/roles/11", True)
    MOBILE_NOTIFICATIONS_RELAY_OPERATOR = (
        20,
        110,
        "https://bisq.network/roles/82",
        True,
    )

    # other
    DOMAIN_NAME_HOLDER = (50, 110, "https://bisq.network/roles/77", False)
    DNS_ADMIN = (20, 110, "https://bisq.network/roles/18", False)
    MEDIATOR = (10, 110, "https://bisq.network/roles/83", True)
    ARBITRATOR = (200, 110, "https://bisq.network/roles/13", True)
    BTC_DONATION_ADDRESS_OWNER = (50, 110, "https://bisq.network/roles/80", True)

    def __init__(
        self,
        required_bond_unit: int,
        unlock_time_in_days: int,
        link: str,
        allow_multiple_holders: bool,
    ):
        """
        Initialize a BondedRoleType instance.

        :param required_bond_unit: Required bond unit for lockup transaction (will be multiplied with PARAM.BONDED_ROLE_FACTOR for BSQ value).
        :param unlock_time_in_days: Unlock time in days.
        :param link: Link to GitHub for role description.
        :param allow_multiple_holders: If the role can be held by multiple persons (e.g., seed nodes vs. domain name).
        """
        # Will be multiplied with PARAM.BONDED_ROLE_FACTOR to get BSQ amount.
        # As BSQ is volatile we need to adjust the bonds over time.
        # To avoid changing the Enum we use the BONDED_ROLE_FACTOR param to react on BSQ price changes.
        # Required bond = requiredBondUnit * PARAM.BONDED_ROLE_FACTOR.value
        self.required_bond_unit = required_bond_unit
        # Unlock time in blocks
        self.unlock_time_in_blocks = (
            unlock_time_in_days * 144  # mainnet (144 blocks per day)
            if Config.BASE_CURRENCY_NETWORK_VALUE.is_mainnet()
            # regtest (arbitrarily low value for dev testing)
            else (
                5 if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest() else 144
            )  # testnet (relatively short time for testing purposes)
        )
        self.link = link
        self.allow_multiple_holders = allow_multiple_holders

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def get_display_string(self):
        return Res.get(f"dao.bond.bondedRoleType.{self.name}")

    def __str__(self):
        return (
            f"BondedRoleType{{\n"
            f"     requiredBondUnit={self.required_bond_unit},\n"
            f"     unlockTime={self.unlock_time_in_blocks},\n"
            f"     link='{self.link}',\n"
            f"     allowMultipleHolders={self.allow_multiple_holders}\n"
            f"}} {super().__str__()}"
        )
