import unittest
from dataclasses import dataclass

from bitcoinj.core.transaction import Transaction
from bitcoinj.params.test_net3_params import TestNet3Params
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.core.network_parameters import NetworkParameters

TESTNET = TestNet3Params()
MAINNET = MainNetParams()
 
class TransactionTest(unittest.TestCase):

    def test_witness_transaction(self):
        # Roundtrip without witness
        hex_str = "0100000003362c10b042d48378b428d60c5c98d8b8aca7a03e1a2ca1048bfd469934bbda95010000008b483045022046c8bc9fb0e063e2fc8c6b1084afe6370461c16cbf67987d97df87827917d42d022100c807fa0ab95945a6e74c59838cc5f9e850714d8850cec4db1e7f3bcf71d5f5ef0141044450af01b4cc0d45207bddfb47911744d01f768d23686e9ac784162a5b3a15bc01e6653310bdd695d8c35d22e9bb457563f8de116ecafea27a0ec831e4a3e9feffffffffc19529a54ae15c67526cc5e20e535973c2d56ef35ff51bace5444388331c4813000000008b48304502201738185959373f04cc73dbbb1d061623d51dc40aac0220df56dabb9b80b72f49022100a7f76bde06369917c214ee2179e583fefb63c95bf876eb54d05dfdf0721ed772014104e6aa2cf108e1c650e12d8dd7ec0a36e478dad5a5d180585d25c30eb7c88c3df0c6f5fd41b3e70b019b777abd02d319bf724de184001b3d014cb740cb83ed21a6ffffffffbaae89b5d2e3ca78fd3f13cf0058784e7c089fb56e1e596d70adcfa486603967010000008b483045022055efbaddb4c67c1f1a46464c8f770aab03d6b513779ad48735d16d4c5b9907c2022100f469d50a5e5556fc2c932645f6927ac416aa65bc83d58b888b82c3220e1f0b73014104194b3f8aa08b96cae19b14bd6c32a92364bea3051cb9f018b03e3f09a57208ff058f4b41ebf96b9911066aef3be22391ac59175257af0984d1432acb8f2aefcaffffffff0340420f00000000001976a914c0fbb13eb10b57daa78b47660a4ffb79c29e2e6b88ac204e0000000000001976a9142cae94ffdc05f8214ccb2b697861c9c07e3948ee88ac1c2e0100000000001976a9146e03561cd4d6033456cc9036d409d2bf82721e9888ac00000000"
        tx = Transaction(MAINNET, bytes.fromhex(hex_str))
        
        self.assertFalse(tx.has_witnesses)
        self.assertEqual(3, len(tx.inputs))
        for tx_in in tx.inputs:
            self.assertFalse(tx_in.has_witness)
        self.assertEqual(3, len(tx.outputs))
        self.assertEqual(hex_str, tx.bitcoin_serialize().hex())
        self.assertEqual("38d4cfeb57d6685753b7a3b3534c3cb576c34ca7344cd4582f9613ebf0c2b02a", tx.get_tx_id(), "Incorrect hash")
        self.assertEqual(tx.get_wtx_id(), tx.get_tx_id())
        self.assertEqual(len(hex_str) // 2, tx.get_message_size())

        # Roundtrip with witness
        hex_str = "0100000000010213206299feb17742091c3cb2ab45faa3aa87922d3c030cafb3f798850a2722bf0000000000feffffffa12f2424b9599898a1d30f06e1ce55eba7fabfeee82ae9356f07375806632ff3010000006b483045022100fcc8cf3014248e1a0d6dcddf03e80f7e591605ad0dbace27d2c0d87274f8cd66022053fcfff64f35f22a14deb657ac57f110084fb07bb917c3b42e7d033c54c7717b012102b9e4dcc33c9cc9cb5f42b96dddb3b475b067f3e21125f79e10c853e5ca8fba31feffffff02206f9800000000001976a9144841b9874d913c430048c78a7b18baebdbea440588ac8096980000000000160014e4873ef43eac347471dd94bc899c51b395a509a502483045022100dd8250f8b5c2035d8feefae530b10862a63030590a851183cb61b3672eb4f26e022057fe7bc8593f05416c185d829b574290fb8706423451ebd0a0ae50c276b87b43012102179862f40b85fa43487500f1d6b13c864b5eb0a83999738db0f7a6b91b2ec64f00db080000"
        tx = Transaction(MAINNET, bytes.fromhex(hex_str))
        
        self.assertTrue(tx.has_witnesses)
        self.assertEqual(2, len(tx.inputs))
        self.assertTrue(tx.inputs[0].has_witness)
        self.assertFalse(tx.inputs[1].has_witness)
        self.assertEqual(2, len(tx.outputs))
        self.assertEqual(hex_str, tx.serialize().hex())
        self.assertEqual("99e7484eafb6e01622c395c8cae7cb9f8822aab6ba993696b39df8b60b0f4b11", tx.get_tx_id(), "Incorrect hash")
        self.assertNotEqual(tx.get_wtx_id(), tx.get_tx_id())
        self.assertEqual(len(hex_str) // 2, tx.get_message_size())

if __name__ == '__main__':
    unittest.main()