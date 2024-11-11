
from bisq.asset.coin import Coin
from bisq.asset.ether_address_validator import EtherAddressValidator


class EtherClassic(Coin):
    
    def __init__(self):
        super().__init__(
            name="Ether Classic",
            ticker_symbol="ETC",
            address_validator=EtherAddressValidator("account.altcoin.popup.validation.ETC"),
        )
        