from bisq.asset.erc20_token import Erc20Token


class EtherStone(Erc20Token):
    def __init__(self):
        super().__init__(
            name="EtherStone",
            ticker_symbol="ETHS",
        )
