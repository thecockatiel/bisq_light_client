from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

class XcpAddressValidator(RegexAddressValidator):
    def __init__(self):
        super().__init__("^[1][a-zA-Z0-9]{33}$", "account.altcoin.popup.validation.XCP")

class Counterparty(Coin):

    def __init__(self):
        super().__init__(
            name="Counterparty",
            ticker_symbol="XCP",
            address_validator=XcpAddressValidator(),
        )
