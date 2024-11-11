
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Doichain(Coin):
    
    class DoichainParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 52
            self.p2sh_header = 13
    
    def __init__(self):
        super().__init__(
            name="Doichain",
            ticker_symbol="DOI",
            address_validator=Base58AddressValidator(self.DoichainParams()),
        )
        