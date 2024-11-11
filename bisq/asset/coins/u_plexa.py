from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.upx.msg")
class uPlexa(Coin):

    def __init__(self):
        super().__init__(
            name="uPlexa",
            ticker_symbol="UPX",
            address_validator=RegexAddressValidator("^((UPX)[1-9A-Za-z^OIl]{95}|(UPi)[1-9A-Za-z^OIl]{106}|(UmV|UmW)[1-9A-Za-z^OIl]{94})$"),
        )

