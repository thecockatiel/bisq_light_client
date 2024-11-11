from bisq.asset.erc20_token import Erc20Token


class TrueUSD(Erc20Token):
    def __init__(self):
        super().__init__(
            name="TrueUSD",
            ticker_symbol="TUSD",
        )
