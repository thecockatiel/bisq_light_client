
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Kekcoin(Coin):
    
    class KekcoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 45
            self.p2sh_header = 88
    
    def __init__(self):
        super().__init__(
            name="Kekcoin",
            ticker_symbol="KEK",
            address_validator=Base58AddressValidator(self.KekcoinParams()),
        )
        