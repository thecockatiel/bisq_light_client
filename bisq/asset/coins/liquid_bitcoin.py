from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.liquid_bitcoin_address_validator import LiquidBitcoinAddressValidator

@alt_coin_account_disclaimer("account.altcoin.popup.liquidbitcoin.msg")
class LiquidBitcoin(Coin):

    def __init__(self):
        super().__init__(
            name="Liquid Bitcoin",
            ticker_symbol="L-BTC",
            address_validator=LiquidBitcoinAddressValidator(),
        )
