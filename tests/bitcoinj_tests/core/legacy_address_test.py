import unittest

from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.params.test_net3_params import TestNet3Params
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.script.script_type import ScriptType

TESTNET = TestNet3Params()
MAINNET = MainNetParams()

class LegacyAddressTest(unittest.TestCase):

    def test_stringification(self):
        a = LegacyAddress.from_pub_key_hash(bytes.fromhex("fda79a24e50ff70ff42f7d89585da5bd19d9e5cc"), TESTNET)
        self.assertEqual("n4eA2nbYqErp7H6jebchxAN59DmNpksexv", str(a))
        self.assertEqual(ScriptType.P2PKH, a.output_script_type)
        
        b = LegacyAddress.from_pub_key_hash(bytes.fromhex("4a22c3c4cbb31e4d03b15550636762bda0baf85a"), MAINNET)
        self.assertEqual("17kzeh4N8g49GFvdDzSf8PjaPfyoD1MndL", str(b))
        self.assertEqual(ScriptType.P2PKH, b.output_script_type)
        
    def test_decoding(self):
        a = LegacyAddress.from_base58("n4eA2nbYqErp7H6jebchxAN59DmNpksexv", TESTNET)
        self.assertEqual("fda79a24e50ff70ff42f7d89585da5bd19d9e5cc", a.hash.hex())
        
        b = LegacyAddress.from_base58("17kzeh4N8g49GFvdDzSf8PjaPfyoD1MndL", MAINNET)
        self.assertEqual("4a22c3c4cbb31e4d03b15550636762bda0baf85a", b.hash.hex())
        
    def test_p2sh_address(self):
        a = LegacyAddress.from_base58("35b9vsyH1KoFT5a5KtrKusaCcPLkiSo1tU", MAINNET)
        self.assertTrue(a.p2sh)
        self.assertEqual(MAINNET.p2sh_header, a.version)
        self.assertEqual(ScriptType.P2SH, a.output_script_type)
        
        b = LegacyAddress.from_base58("2MuVSxtfivPKJe93EC1Tb9UhJtGhsoWEHCe", TESTNET)
        self.assertTrue(b.p2sh)
        self.assertEqual(TESTNET.p2sh_header, b.version)
        self.assertEqual(ScriptType.P2SH, b.output_script_type)


if __name__ == '__main__':
    unittest.main()