
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Spectrecoin(Coin):
    
    class SpectrecoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 63
            self.p2sh_header = 136
    
    def __init__(self):
        super().__init__(
            name="Spectrecoin",
            ticker_symbol="XSPEC",
            address_validator=Base58AddressValidator(self.SpectrecoinParams()),
        )
        