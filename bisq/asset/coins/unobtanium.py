from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

class UnobtaniumAddressValidator(RegexAddressValidator):
    def __init__(self):
        super().__init__("^[u]?[a-zA-Z0-9]{33}$", "account.altcoin.popup.validation.UNO")

class Unobtanium(Coin):

    def __init__(self):
        super().__init__(
            name="Unobtanium",
            ticker_symbol="UNO",
            address_validator=UnobtaniumAddressValidator(),
        )
