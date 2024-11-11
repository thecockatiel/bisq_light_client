from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin


class Starwels(Coin):

    def __init__(self):
        super().__init__(
            name="Starwels",
            ticker_symbol="USDH",
            address_validator=Base58AddressValidator(),
        )
