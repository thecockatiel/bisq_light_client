
from enum import Enum

from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.params.reg_test_params import RegTestParams
from bitcoinj.params.test_net3_params import TestNet3Params


class BaseCurrencyNetwork(Enum):
    BTC_MAINNET = MainNetParams(), "BTC", "MAINNET", "Bitcoin"
    BTC_TESTNET = TestNet3Params(), "BTC", "MAINNET", "Bitcoin"
    BTC_REGTEST = RegTestParams(), "BTC", "MAINNET", "Bitcoin"
    BTC_DAO_TESTNET = TestNet3Params(), "BTC", "MAINNET", "Bitcoin" #  server side regtest until v0.9.5
    BTC_DAO_BETANET = MainNetParams(), "BTC", "MAINNET", "Bitcoin" # mainnet test genesis
    BTC_DAO_REGTEST = RegTestParams(), "BTC", "MAINNET", "Bitcoin" # server side regtest after v0.9.5, had breaking code changes so we started over again
    
    def __init__(self, parameters: NetworkParameters, currency_code: str, network: str, currency_name: str):
        self.parameters = parameters
        self.currency_code = currency_code
        self.network = network
        self.currency_name = currency_name

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def __str__(self):
        return f"BaseCurrencyNetwork(parameters='{self.parameters}', currency_code='{self.currency_code}', network='{self.network}', currency_name='{self.currency_name}')"
    
    def is_mainnet(self):
        return self.name == "BTC_MAINNET"
    
    def is_testnet(self):
        return self.name == "BTC_TESTNET"
    
    def is_regtest(self):
        return self.name == "BTC_REGTEST"
    
    def is_dao_testnet(self):
        return self.name == "BTC_DAO_TESTNET"
    
    def is_dao_regtest(self):
        return self.name == "BTC_DAO_REGTEST"
    
    def is_dao_betanet(self):
        return self.name == "BTC_DAO_BETANET"
    
    def get_default_min_fee_per_v_byte(self):
        # 2021-02-22 due to mempool congestion, increased from 2
        return 15
