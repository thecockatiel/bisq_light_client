
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Animecoin(Coin):
    
    class AnimecoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 23
            self.p2sh_header = 9
    
    def __init__(self):
        super().__init__(
            name="Animecoin",
            ticker_symbol="ACM",
            address_validator=Base58AddressValidator(self.AnimecoinParams()),
        )
        