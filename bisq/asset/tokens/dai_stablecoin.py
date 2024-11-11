from bisq.asset.erc20_token import Erc20Token


class DaiStablecoin(Erc20Token):
    def __init__(self):
        super().__init__(
            name="Dai Stablecoin",
            ticker_symbol="DAI",
        )
