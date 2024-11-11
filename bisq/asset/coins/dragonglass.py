from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator

@alt_coin_account_disclaimer("account.altcoin.popup.drgl.msg")
class Dragonglass(Coin):
    
    def __init__(self):
        super().__init__(
            name="Dragonglass",
            ticker_symbol="DRGL",
            address_validator=RegexAddressValidator("^(dRGL)[1-9A-HJ-NP-Za-km-z]{94}$"),
        )
