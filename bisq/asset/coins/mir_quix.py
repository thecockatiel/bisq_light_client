from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class MirQuiX(Coin):

    def __init__(self):
        super().__init__(
            name="MirQuiX",
            ticker_symbol="MQX",
            address_validator=RegexAddressValidator("^[M][a-km-zA-HJ-NP-Z1-9]{33}$"),
        )

