from bisq.asset.bitcoin_address_validator import BitcoinAddressValidator
from bisq.asset.coin import Coin
from electrum_min.constants import AbstractNet, BitcoinMainnet, BitcoinRegtest, BitcoinTestnet


class Bitcoin(Coin):
    
    def __init__(self, network: Coin.Network, net: AbstractNet):
        super().__init__(
            name="Bitcoin",
            ticker_symbol="BTC",    
            address_validator=BitcoinAddressValidator(net),
            network=network,
        )
    
    Mainnet = lambda: Bitcoin(Coin.Network.MAINNET, BitcoinMainnet())
    Testnet = lambda: Bitcoin(Coin.Network.TESTNET, BitcoinTestnet())
    Regtest = lambda: Bitcoin(Coin.Network.REGTEST, BitcoinRegtest())