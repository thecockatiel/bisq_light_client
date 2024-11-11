
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Lytix(Coin):
    
    class LytixParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 19
            self.p2sh_header = 11
    
    def __init__(self):
        super().__init__(
            name="Lytix",
            ticker_symbol="LYTX",
            address_validator=Base58AddressValidator(self.LytixParams()),
        )
        