
from bisq.asset.coin import Coin
from bisq.asset.ether_address_validator import EtherAddressValidator


class RSKSmartBitcoin(Coin):
    
    def __init__(self):
        super().__init__(
            name="RSK Smart Bitcoin",
            ticker_symbol="R-BTC",
            address_validator=EtherAddressValidator("account.altcoin.popup.validation.RBTC"),
        )
        