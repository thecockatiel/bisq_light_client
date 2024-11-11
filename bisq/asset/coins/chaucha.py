
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Chaucha(Coin):
    
    class ChauchaParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 88
            self.p2sh_header = 50
    
    def __init__(self):
        super().__init__(
            name="Chaucha",
            ticker_symbol="CHA",
            address_validator=Base58AddressValidator(self.ChauchaParams()),
        )
        