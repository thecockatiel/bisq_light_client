from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class PENG(Coin):

    def __init__(self):
        super().__init__(
            name="PENG Coin",
            ticker_symbol="PENG",
            address_validator=RegexAddressValidator("^[P][a-km-zA-HJ-NP-Z1-9]{33}$"),
        )

