from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class ZelCash(Coin):

    def __init__(self):
        super().__init__(
            name="ZelCash",
            ticker_symbol="ZEL",
            address_validator=RegexAddressValidator(
                "^t.*", "validation.altcoin.zAddressesNotSupported"
            ),
        )
