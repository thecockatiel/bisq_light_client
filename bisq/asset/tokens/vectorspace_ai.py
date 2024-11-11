from bisq.asset.erc20_token import Erc20Token


class VectorspaceAI(Erc20Token):
    def __init__(self):
        super().__init__(
            name="VectorspaceAI",
            ticker_symbol="VXV",
        )
