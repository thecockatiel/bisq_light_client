
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class LitecoinPlus(Coin):
    
    class LitecoinPlusParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 75
            self.p2sh_header = 8
    
    def __init__(self):
        super().__init__(
            name="LitecoinPlus",
            ticker_symbol="LCP",
            address_validator=Base58AddressValidator(self.LitecoinPlusParams()),
        )
        