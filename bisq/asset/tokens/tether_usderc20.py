from bisq.asset.erc20_token import Erc20Token


class TetherUSDERC20(Erc20Token):
    def __init__(self):
        super().__init__(
            name="Tether USD (ERC20)",
            ticker_symbol="USDT-E",
        )
