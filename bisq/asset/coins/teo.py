from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class TEO(Coin):

    def __init__(self):
        super().__init__(
            name="Trust Ether reOrigin",
            ticker_symbol="TEO",
            address_validator=RegexAddressValidator("^0x[0-9a-fA-F]{40}$"),
        )

