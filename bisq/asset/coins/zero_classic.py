from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class ZeroClassic(Coin):

    def __init__(self):
        super().__init__(
            name="ZeroClassic",
            ticker_symbol="ZERC",
            address_validator=RegexAddressValidator(
                "^t.*", "validation.altcoin.zAddressesNotSupported"
            ),
        )
