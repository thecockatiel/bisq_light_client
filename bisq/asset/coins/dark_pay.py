
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class DarkPay(Coin):
    
    class DarkPayMainNetParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 31
            self.p2sh_header = 60
    
    def __init__(self):
        super().__init__(
            name="DarkPay",
            ticker_symbol="D4RK",
            address_validator=Base58AddressValidator(self.DarkPayMainNetParams()),
        )
        