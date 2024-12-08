
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.params.test_net3_params import TestNet3Params


NETWORKS: set[NetworkParameters] = {MainNetParams(), TestNet3Params()}
