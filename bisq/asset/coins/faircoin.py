
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Faircoin(Coin):
    
    class FaircoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 95
            self.p2sh_header = 36
    
    def __init__(self):
        super().__init__(
            name="Faircoin",
            ticker_symbol="FAIR",
            address_validator=Base58AddressValidator(self.FaircoinParams()),
        )
        