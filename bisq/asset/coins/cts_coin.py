
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class CTSCoin(Coin):
    
    class CTSCoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 66
            self.p2sh_header = 16
    
    def __init__(self):
        super().__init__(
            name="CTSCoin",
            ticker_symbol="CTSC",
            address_validator=Base58AddressValidator(self.CTSCoinParams()),
        )
        