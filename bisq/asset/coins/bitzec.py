from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Bitzec(Coin):

    def __init__(self):
        super().__init__(
            name="Bitzec",
            ticker_symbol="BZC",
            address_validator=RegexAddressValidator("^t.*$", "validation.altcoin.zAddressesNotSupported"),
        )

