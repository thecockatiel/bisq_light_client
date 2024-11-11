from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class LitecoinZ(Coin):

    def __init__(self):
        super().__init__(
            name="LitecoinZ",
            ticker_symbol="LTZ",
            address_validator=RegexAddressValidator("^L.*$", "validation.altcoin.ltz.zAddressesNotSupported"),
        )

