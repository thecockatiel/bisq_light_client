from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

class ZcoinAddressValidator(RegexAddressValidator):
    def __init__(self):
        super().__init__("^a?[a-zA-Z0-9]{33}$", "account.altcoin.popup.validation.XZC")

@alt_coin_account_disclaimer("account.altcoin.popup.XZC.msg")
class Zcoin(Coin):

    def __init__(self):
        super().__init__(
            name="Zcoin",
            ticker_symbol="XZC",
            address_validator=ZcoinAddressValidator(),
        )
