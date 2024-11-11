
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Emercoin(Coin):
    
    class EmercoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 33
            self.p2sh_header = 92
    
    def __init__(self):
        super().__init__(
            name="Emercoin",
            ticker_symbol="EMC",
            address_validator=Base58AddressValidator(self.EmercoinParams()),
        )
        