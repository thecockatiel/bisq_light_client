from bisq.asset.coin import Coin
from bisq.asset.coins.mile import MileAddressValidator


class XDR(Coin):

    def __init__(self):
        super().__init__(
            name="XDR",
            ticker_symbol="XDR0",
            address_validator=MileAddressValidator(),
        )
