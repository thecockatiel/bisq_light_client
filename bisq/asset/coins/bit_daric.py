from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class BitDaric(Coin):

    def __init__(self):
        super().__init__(
            name="BitDaric",
            ticker_symbol="DARX",
            address_validator=RegexAddressValidator("^[R][a-km-zA-HJ-NP-Z1-9]{25,34}$"),
        )

