
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Pinkcoin(Coin):
    
    class PinkcoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 3
            self.p2sh_header = 28
    
    def __init__(self):
        super().__init__(
            name="Pinkcoin",
            ticker_symbol="PINK",
            address_validator=Base58AddressValidator(self.PinkcoinParams()),
        )
        