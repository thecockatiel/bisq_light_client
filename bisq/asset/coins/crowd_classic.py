from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class CRowdCLassic(Coin):

    def __init__(self):
        super().__init__(
            name="CRowdCLassic",
            ticker_symbol="CRCL",
            address_validator=RegexAddressValidator("^[C][a-zA-Z0-9]{33}$"),
        )

