from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Amitycoin(Coin):

    def __init__(self):
        super().__init__(
            name="Amitycoin",
            ticker_symbol="AMIT",
            address_validator=RegexAddressValidator("^amit[1-9A-Za-z^OIl]{{94}}"),
        )
