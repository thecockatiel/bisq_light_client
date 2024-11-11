
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Navcoin(Coin):
    
    class NavcoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 53
            self.p2sh_header = 85
    
    def __init__(self):
        super().__init__(
            name="Navcoin",
            ticker_symbol="NAV",
            address_validator=Base58AddressValidator(self.NavcoinParams()),
        )
        