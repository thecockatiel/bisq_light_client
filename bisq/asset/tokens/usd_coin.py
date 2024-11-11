from bisq.asset.erc20_token import Erc20Token


class USDCoin(Erc20Token):
    def __init__(self):
        super().__init__(
            name="USD Coin",
            ticker_symbol="USDC",
        )
