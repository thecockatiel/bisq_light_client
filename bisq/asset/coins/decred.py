from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

class DecredAddressValidator(RegexAddressValidator):
    def __init__(self):
        super().__init__("^[Dk|Ds|De|DS|Dc|Pm][a-zA-Z0-9]{24,34}$", "account.altcoin.popup.validation.DCR")

class Decred(Coin):

    def __init__(self):
        super().__init__(
            name="Decred",
            ticker_symbol="DCR",
            address_validator=DecredAddressValidator(),
        )
