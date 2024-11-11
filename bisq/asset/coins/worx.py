from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class WORX(Coin):

    def __init__(self):
        super().__init__(
            name="WORX Coin",
            ticker_symbol="WORX",
            address_validator=RegexAddressValidator("^[W][a-km-zA-HJ-NP-Z1-9]{33}$"),
        )

