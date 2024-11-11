from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Persona(Coin):

    def __init__(self):
        super().__init__(
            name="Persona",
            ticker_symbol="PRSN",
            address_validator=RegexAddressValidator("^[P][a-km-zA-HJ-NP-Z1-9]{33}$"),
        )

