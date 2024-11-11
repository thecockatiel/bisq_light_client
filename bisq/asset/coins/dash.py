
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Dash(Coin):
    
    class DashMainNetParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 76
            self.p2sh_header = 16
    
    def __init__(self):
        super().__init__(
            name="Dash",
            ticker_symbol="DASH",
            address_validator=Base58AddressValidator(self.DashMainNetParams()),
            network=self.Network.MAINNET,
        )
        