from bisq.asset.erc20_token import Erc20Token


class AugmintEuro(Erc20Token):
    def __init__(self):
        super().__init__(
            name="Augmint Euro",
            ticker_symbol="AEUR",
        )
