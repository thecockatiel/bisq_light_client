
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class Bitmark(Coin):
    
    class BitmarkParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 85
            self.p2sh_header = 5
    
    def __init__(self):
        super().__init__(
            name="Bitmark",
            ticker_symbol="BTM",
            address_validator=Base58AddressValidator(self.BitmarkParams()),
        )
        