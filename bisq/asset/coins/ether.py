
from bisq.asset.coin import Coin
from bisq.asset.ether_address_validator import EtherAddressValidator


class Ether(Coin):
    
    def __init__(self):
        super().__init__(
            name="Ether",
            ticker_symbol="ETH",
            address_validator=EtherAddressValidator(),
        )
        