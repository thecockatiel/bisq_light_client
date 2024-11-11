
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class BitcoinRhodium(Coin):
    
    class BitcoinRhodiumParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 61
            self.p2sh_header = 123
    
    def __init__(self):
        super().__init__(
            name="XRhodium",
            ticker_symbol="XRC",
            address_validator=Base58AddressValidator(self.BitcoinRhodiumParams()),
        )
        