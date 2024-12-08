from bisq.asset.bitcoin_address_validator import BitcoinAddressValidator
from bisq.asset.coin import Coin
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.params.reg_test_params import RegTestParams
from bitcoinj.params.test_net3_params import TestNet3Params


class Bitcoin(Coin):
    
    def __init__(self, network: Coin.Network, network_parameters: NetworkParameters):
        super().__init__(
            name="Bitcoin",
            ticker_symbol="BTC",    
            address_validator=BitcoinAddressValidator(network_parameters),
            network=network,
        )
    
    Mainnet = lambda: Bitcoin(Coin.Network.MAINNET, MainNetParams())
    Testnet = lambda: Bitcoin(Coin.Network.TESTNET, TestNet3Params())
    Regtest = lambda: Bitcoin(Coin.Network.REGTEST, RegTestParams())