from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.blk-burnt.msg")
class BurntBlackCoin(Coin):
    PAYLOAD_LIMIT = 15000
    
    def __init__(self):
        super().__init__(
            name="Burnt BlackCoin",
            ticker_symbol="BLK-BURNT",
            address_validator=RegexAddressValidator(f"^(?:[0-9a-z]{{2}}?){{1,{2 * self.PAYLOAD_LIMIT}}}$"),
        )
