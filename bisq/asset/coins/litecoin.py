from bisq.asset.bitcoin_address_validator import BitcoinAddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Litecoin(Coin):

    class LitecoinMainNetParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 48
            self.p2sh_header = 50
            self.segwit_address_hrp = "ltc"

    def __init__(self):
        super().__init__(
            name="Litecoin",
            ticker_symbol="LTC",
            address_validator=BitcoinAddressValidator(self.LitecoinMainNetParams()),
        )
