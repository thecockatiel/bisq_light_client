
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter


class LBRYCredits(Coin):
    
    class LBRYCreditsMainNetParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 0x55
            self.p2sh_header = 0x7a
    
    def __init__(self):
        super().__init__(
            name="LBRYCredits",
            ticker_symbol="LBC",
            address_validator=Base58AddressValidator(self.LBRYCreditsMainNetParams()),
            network=self.Network.MAINNET,
        )
        