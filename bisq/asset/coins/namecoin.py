from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

class NamecoinAddressValidator(RegexAddressValidator):
    def __init__(self):
        super().__init__("^[NM][a-zA-Z0-9]{33}$", "account.altcoin.popup.validation.NMC")

class Namecoin(Coin):

    def __init__(self):
        super().__init__(
            name="Namecoin",
            ticker_symbol="NMC",
            address_validator=NamecoinAddressValidator(),
        )
