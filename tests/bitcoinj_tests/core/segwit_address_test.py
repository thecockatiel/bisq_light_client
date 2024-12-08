import unittest
from dataclasses import dataclass

from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.params.test_net3_params import TestNet3Params
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.script.script_builder import ScriptBuilder
from bitcoinj.script.script_type import ScriptType
from electrum_min.segwit_addr import decode_segwit_address

TESTNET = TestNet3Params()
MAINNET = MainNetParams()

@dataclass
class AddressData:
    address: str
    expected_params: object
    expected_script_pubkey: str
    expected_witness_version: int

    def __str__(self):
        return f"AddressData(address={self.address}, params={self.expected_params.get_id()}, " \
               f"scriptPubKey={self.expected_script_pubkey}, witnessVersion={self.expected_witness_version})"

class LegacyAddressTest(unittest.TestCase):

    def test_example_p2wpkh_mainnet(self):
        bech32 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        address = SegwitAddress.from_bech32(bech32, MAINNET)
        
        self.assertEqual(MAINNET, address.params)
        self.assertEqual(ScriptType.P2WPKH, address.output_script_type)
        self.assertEqual(bech32, str(address))
        self.assertEqual("0014751e76e8199196d454941c45d1b3a323f1433bd6", ScriptBuilder.create_output_script(address).hex())

    def test_example_p2wsh_mainnet(self):
        bech32 = "bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3"
        address = SegwitAddress.from_bech32(bech32, MAINNET)
        
        self.assertEqual(MAINNET, address.params)
        self.assertEqual(ScriptType.P2WSH, address.output_script_type)
        self.assertEqual(bech32, str(address))
        self.assertEqual("00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262", ScriptBuilder.create_output_script(address).hex())
    

    def test_example_p2wpkh_testnet(self):
        bech32 = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        address = SegwitAddress.from_bech32(bech32, TESTNET)
        
        self.assertEqual(TESTNET, address.params)
        self.assertEqual(ScriptType.P2WPKH, address.output_script_type)
        self.assertEqual(bech32, str(address))
        self.assertEqual("0014751e76e8199196d454941c45d1b3a323f1433bd6", ScriptBuilder.create_output_script(address).hex())
        
    def test_example_p2wsh_testnet(self):
        bech32 = "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
        address = SegwitAddress.from_bech32(bech32, TESTNET)
        
        self.assertEqual(TESTNET, address.params)
        self.assertEqual(ScriptType.P2WSH, address.output_script_type)
        self.assertEqual(bech32, str(address))
        self.assertEqual("00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262", ScriptBuilder.create_output_script(address).hex())
    
    VALID_ADDRESSES = [
        # from BIP350 (includes the corrected BIP173 vectors):
        AddressData("BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", MAINNET,
                "0014751e76e8199196d454941c45d1b3a323f1433bd6", 0),
        AddressData("tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7", TESTNET,
                "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262", 0),
        AddressData("BC1SW50QGDZ25J", MAINNET, "6002751e", 16),
        AddressData("bc1zw508d6qejxtdg4y5r3zarvaryvaxxpcs", MAINNET, 
                "5210751e76e8199196d454941c45d1b3a323", 2),
        AddressData("tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy", TESTNET,
                "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433", 0),
        AddressData("tb1pqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesf3hn0c", TESTNET,
                "5120000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433", 1),
        AddressData("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0", MAINNET,
                "512079be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798", 1),
    ]

    INVALID_ADDRESSES = [
        # from BIP173:
        "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",  # Invalid human-readable part
        "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5",  # Invalid checksum
        "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",  # Invalid witness version
        "bc1rw5uspcuh",  # Invalid program length
        "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",  # Invalid program length
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",  # Invalid program length for witness version 0 (per BIP141)
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7",  # Mixed case
        "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du",  # Zero padding of more than 4 bits
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv",  # Non-zero padding in 8-to-5 conversion
        "bc1gmk9yu",  # Empty data section
        # from BIP350:
        "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",  # Invalid human-readable part
        "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5",  # Invalid checksum
        "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",  # Invalid witness version
        "bc1rw5uspcuh",  # Invalid program length
        "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",  # Invalid program length
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",  # Invalid program length for witness version 0 (per BIP141)
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7",  # Mixed case
        "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du",  # zero padding of more than 4 bits
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv",  # Non-zero padding in 8-to-5 conversion
        "bc1gmk9yu",  # Empty data section
    ]

    def test_valid_addresses(self):
        for data in self.VALID_ADDRESSES:
            with self.subTest(data=data):
                address = SegwitAddress.from_bech32(data.address.lower(), data.expected_params)
                self.assertEqual(data.expected_params, address.params)
                self.assertEqual(data.expected_script_pubkey, 
                               ScriptBuilder.create_output_script(address).hex())

    def test_invalid_addresses(self):
        for addr in self.INVALID_ADDRESSES:
            with self.subTest(address=addr):
                with self.assertRaises(Exception):
                    if addr.startswith('bc'):
                        SegwitAddress.from_bech32(addr, MAINNET)
                    else:
                        SegwitAddress.from_bech32(addr, TESTNET)

if __name__ == '__main__':
    unittest.main()