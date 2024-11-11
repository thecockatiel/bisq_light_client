
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Galilel(Coin):
    
    class GalilelParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 68
            self.p2sh_header = 16
    
    def __init__(self):
        super().__init__(
            name="Galilel",
            ticker_symbol="GALI",
            address_validator=Base58AddressValidator(self.GalilelParams()),
        )
        