
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Fujicoin(Coin):
    
    class FujicoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 36
            self.p2sh_header = 16
    
    def __init__(self):
        super().__init__(
            name="Fujicoin",
            ticker_symbol="FJC",
            address_validator=Base58AddressValidator(self.FujicoinParams()),
        )
        