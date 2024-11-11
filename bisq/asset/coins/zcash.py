from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.ZEC.msg")
class Zcash(Coin):

    def __init__(self):
        super().__init__(
            name="Zcash",
            ticker_symbol="ZEC",
            address_validator=RegexAddressValidator("^t.*", "validation.altcoin.zAddressesNotSupported"),
        )

