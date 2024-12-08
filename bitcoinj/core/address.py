from bitcoinj.core.network_parameters import MainNetParams, NetworkParameters
from electrum_min.bitcoin import b58_address_to_hash160
from electrum_min.segwit_addr import decode_segwit_address

#TODO
class Address:
    
    @staticmethod
    def is_b58_address(addr: str, network_parameters: NetworkParameters=None) -> bool:
        # a slightly modified version of electrum's, to work with bitcoinj style NetworkParameters:
        if network_parameters is None: network_parameters = MainNetParams()
        try:
            # test length, checksum, encoding:
            addrtype, h = b58_address_to_hash160(addr)
        except Exception as e:
            return False
        if addrtype not in [network_parameters.address_header, network_parameters.p2sh_header]:
            return False
        return True
    
    @staticmethod
    def is_segwit_address(addr: str, network_parameters: NetworkParameters=None) -> bool:
        if network_parameters is None: network_parameters = MainNetParams()
        try:
            witver, witprog = decode_segwit_address(network_parameters.segwit_address_hrp, addr)
        except Exception as e:
            return False
        return witprog is not None