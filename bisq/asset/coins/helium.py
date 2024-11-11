
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Helium(Coin):
    
    class HeliumParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 63
            self.p2sh_header = 5
    
    def __init__(self):
        super().__init__(
            name="Helium",
            ticker_symbol="HLM",
            address_validator=Base58AddressValidator(self.HeliumParams()),
        )
        