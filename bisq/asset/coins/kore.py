
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Kore(Coin):
    
    class KoreMainNetParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 45
            self.p2sh_header = 85
    
    def __init__(self):
        super().__init__(
            name="Kore",
            ticker_symbol="KORE",
            address_validator=Base58AddressValidator(self.KoreMainNetParams()),
        )
        