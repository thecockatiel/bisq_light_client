from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class CloakCoin(Coin):

    def __init__(self):
        super().__init__(
            name="CloakCoin",
            ticker_symbol="CLOAK",
            address_validator=RegexAddressValidator("^[B|C][a-km-zA-HJ-NP-Z1-9]{33}$|^smY[a-km-zA-HJ-NP-Z1-9]{99}$"),
        )
