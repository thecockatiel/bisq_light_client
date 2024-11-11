
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class KnowYourDeveloper(Coin):
    
    class KydMainNetParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 78
            self.p2sh_header = 85
    
    def __init__(self):
        super().__init__(
            name="Know Your Developer",
            ticker_symbol="KYDC",
            address_validator=Base58AddressValidator(self.KydMainNetParams()),
        )
        