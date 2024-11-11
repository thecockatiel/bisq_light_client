from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class NoteBlockchain(Coin):

    def __init__(self):
        super().__init__(
            name="NoteBlockchain",
            ticker_symbol="NTBC",
            address_validator=RegexAddressValidator("^[N][a-km-zA-HJ-NP-Z1-9]{26,33}$"),
        )

