from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Ryo(Coin):

    def __init__(self):
        super().__init__(
            name="Ryo",
            ticker_symbol="RYO",
            address_validator=RegexAddressValidator("^((RYoL|RYoS)[1-9A-HJ-NP-Za-km-z]{95}|(RYoK)[1-9A-HJ-NP-Za-km-z]{51})$"),
        )

