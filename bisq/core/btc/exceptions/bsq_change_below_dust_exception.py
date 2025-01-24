from bitcoinj.base.coin import Coin


class BsqChangeBelowDustException(Exception):

    def __init__(self, message: str, output_value: Coin):
        super().__init__(message)

        self.output_value = output_value
