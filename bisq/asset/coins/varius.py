from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class VARIUS(Coin):

    def __init__(self):
        super().__init__(
            name="VARIUS Coin",
            ticker_symbol="VARIUS",
            address_validator=RegexAddressValidator("^[V][a-km-zA-HJ-NP-Z1-9]{33}$"),
        )

