from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

class SiafundAddressValidator(RegexAddressValidator):
    def __init__(self):
        super().__init__("^[0-9a-fA-F]{76}$", "account.altcoin.popup.validation.XCP")

class Siafund(Coin):

    def __init__(self):
        super().__init__(
            name="Siafund",
            ticker_symbol="SF",
            address_validator=SiafundAddressValidator(),
        )
