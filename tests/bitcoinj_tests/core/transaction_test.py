import unittest
from dataclasses import dataclass

from bisq.common.crypto.hash import get_sha256_hash
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bitcoinj.core.block import Block
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.transaction_input import TransactionInput
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.core.transaction_witness import TransactionWitness
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.params.test_net3_params import TestNet3Params
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.script.script import Script
from electrum_min.crypto import hash_160
from electrum_min.transaction import PartialTxInput, TxInput, TxOutpoint
from bitcoinj.script.script_builder import ScriptBuilder
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.crypto.transaction_signature import TransactionSignature
from electrum_ecc import ECPrivkey

TESTNET = TestNet3Params()
MAINNET = MainNetParams()


example_tx_hex = "0100000003362c10b042d48378b428d60c5c98d8b8aca7a03e1a2ca1048bfd469934bbda95010000008b483045022046c8bc9fb0e063e2fc8c6b1084afe6370461c16cbf67987d97df87827917d42d022100c807fa0ab95945a6e74c59838cc5f9e850714d8850cec4db1e7f3bcf71d5f5ef0141044450af01b4cc0d45207bddfb47911744d01f768d23686e9ac784162a5b3a15bc01e6653310bdd695d8c35d22e9bb457563f8de116ecafea27a0ec831e4a3e9feffffffffc19529a54ae15c67526cc5e20e535973c2d56ef35ff51bace5444388331c4813000000008b48304502201738185959373f04cc73dbbb1d061623d51dc40aac0220df56dabb9b80b72f49022100a7f76bde06369917c214ee2179e583fefb63c95bf876eb54d05dfdf0721ed772014104e6aa2cf108e1c650e12d8dd7ec0a36e478dad5a5d180585d25c30eb7c88c3df0c6f5fd41b3e70b019b777abd02d319bf724de184001b3d014cb740cb83ed21a6ffffffffbaae89b5d2e3ca78fd3f13cf0058784e7c089fb56e1e596d70adcfa486603967010000008b483045022055efbaddb4c67c1f1a46464c8f770aab03d6b513779ad48735d16d4c5b9907c2022100f469d50a5e5556fc2c932645f6927ac416aa65bc83d58b888b82c3220e1f0b73014104194b3f8aa08b96cae19b14bd6c32a92364bea3051cb9f018b03e3f09a57208ff058f4b41ebf96b9911066aef3be22391ac59175257af0984d1432acb8f2aefcaffffffff0340420f00000000001976a914c0fbb13eb10b57daa78b47660a4ffb79c29e2e6b88ac204e0000000000001976a9142cae94ffdc05f8214ccb2b697861c9c07e3948ee88ac1c2e0100000000001976a9146e03561cd4d6033456cc9036d409d2bf82721e9888ac00000000"


class TransactionTest(unittest.TestCase):

    def test_empty_outputs(self):
        # Create a transaction with inputs but no outputs
        # First create a transaction with some dummy data
        tx = Transaction(TESTNET, bytes.fromhex(example_tx_hex))

        # Clear all outputs
        tx.clear_outputs()

        # Verify should raise an exception due to empty outputs
        with self.assertRaises(VerificationException.EmptyInputsOrOutputs):
            Transaction.verify(TESTNET, tx)

    def test_empty_inputs(self):
        # Create a transaction with outputs but no inputs
        # First create a transaction with some dummy data
        tx = Transaction(TESTNET, bytes.fromhex(example_tx_hex))

        # Clear all inputs
        tx._electrum_transaction._inputs = []
        tx.inputs.invalidate()

        # Verify should raise an exception due to empty inputs
        with self.assertRaises(VerificationException.EmptyInputsOrOutputs):
            Transaction.verify(TESTNET, tx)

    def test_too_large_transaction(self):

        # Create a transaction with some dummy data
        tx = Transaction(TESTNET, bytes.fromhex(example_tx_hex))

        # Make one of the inputs have a huge script
        huge_script = bytes([0] * Block.MAX_BLOCK_SIZE)
        tx.inputs[0].script_sig = huge_script

        # Verify should raise an exception due to transaction being too large
        with self.assertRaises(VerificationException.LargerThanMaxBlockSize):
            Transaction.verify(TESTNET, tx)

    def test_duplicate_out_point(self):
        # Create a transaction with some dummy data
        tx = Transaction(TESTNET)

        tx.add_output(
            TransactionOutput.from_coin_and_address(
                Coin.value_of(1),
                "tb1qglzsh2l7t3ufhtakjcfulv7jhy8plnhvwd28pu",
                tx,  # random address
            ),
        )

        original_input = TransactionInput.from_electrum_input(
            TESTNET,
            TxInput(
                prevout=TxOutpoint(
                    bytes.fromhex(
                        "38d4cfeb57d6685753b7a3b3534c3cb576c34ca7344cd4582f9613ebf0c2b02a"
                    ),
                    0,
                ),
                script_sig=bytes([0]),
            ),
            tx,
        )

        # Add the same input again to create a duplicate
        tx.add_input(original_input)
        tx.add_input(original_input)

        # Verify should raise an exception due to duplicate inputs
        with self.assertRaises(VerificationException.DuplicatedOutPoint):
            Transaction.verify(TESTNET, tx)

    def test_negative_output(self):
        # Create a transaction with some dummy data
        tx = Transaction(TESTNET)

        tx.add_output(
            TransactionOutput.from_coin_and_address(
                Coin.value_of(-1),
                "tb1qglzsh2l7t3ufhtakjcfulv7jhy8plnhvwd28pu",
                tx,  # random address
            ),
        )

        original_input = TransactionInput.from_electrum_input(
            TESTNET,
            TxInput(
                prevout=TxOutpoint(
                    bytes.fromhex(
                        "38d4cfeb57d6685753b7a3b3534c3cb576c34ca7344cd4582f9613ebf0c2b02a"
                    ),
                    0,
                ),
                script_sig=bytes([0]),
            ),
            tx,
        )

        tx.add_input(original_input)

        # Verify should raise an exception due to duplicate inputs
        with self.assertRaises(VerificationException.NegativeValueOutput):
            Transaction.verify(TESTNET, tx)

    def test_witness_transaction(self):
        # Roundtrip without witness
        hex_str = example_tx_hex
        tx = Transaction(MAINNET, bytes.fromhex(hex_str))

        self.assertFalse(tx.has_witnesses)
        self.assertEqual(3, len(tx.inputs))
        for tx_in in tx.inputs:
            self.assertFalse(tx_in.has_witness)
        self.assertEqual(3, len(tx.outputs))
        self.assertEqual(hex_str, tx.bitcoin_serialize().hex())
        self.assertEqual(
            "38d4cfeb57d6685753b7a3b3534c3cb576c34ca7344cd4582f9613ebf0c2b02a",
            tx.get_tx_id(),
            "Incorrect hash",
        )
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
        self.assertEqual(
            "99e7484eafb6e01622c395c8cae7cb9f8822aab6ba993696b39df8b60b0f4b11",
            tx.get_tx_id(),
            "Incorrect hash",
        )
        self.assertNotEqual(tx.get_wtx_id(), tx.get_tx_id())
        self.assertEqual(len(hex_str) // 2, tx.get_message_size())

    def test_witness_signature_p2wpkh(self):
        # Test vector P2WPKH from:
        # https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki

        # Create the unsigned transaction
        tx_hex = (
            "01000000"  # version
            + "02"  # num txIn
            + "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f"
            + "00000000"
            + "00"
            + "eeffffff"  # txIn
            + "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a"
            + "01000000"
            + "00"
            + "ffffffff"  # txIn
            + "02"  # num txOut
            + "202cb20600000000"
            + "1976a914"
            + "8280b37df378db99f66f85c95a783a76ac7a6d59"
            + "88ac"  # txOut
            + "9093510d00000000"
            + "1976a914"
            + "3bde42dbee7e4dbe6a21b2d50ce2f0167faa8159"
            + "88ac"  # txOut
            + "11000000"
        )  # nLockTime
        tx = Transaction(MAINNET, bytes.fromhex(tx_hex))

        self.assertEqual(tx_hex, tx.bitcoin_serialize().hex())
        self.assertEqual(len(tx_hex) // 2, tx.get_message_size())
        self.assertEqual(2, len(tx.inputs))
        self.assertEqual(2, len(tx.outputs))
        tx_in0 = tx.inputs[0]
        tx_in1 = tx.inputs[1]

        key0 = ECPrivkey(
            bytes.fromhex(
                "bbc27228ddcb9209d7fd6f36b02f7dfa6252af40bb2f1cbc7a557da8027ff866"
            )
        )
        script_pub_key0 = ScriptBuilder.create_p2pk_output_script(
            key0.get_public_key_bytes()
        )
        self.assertEqual(
            "2103c9f4836b9a4f77fc0d81f7bcb01b7f1b35916864b9476c241ce9fc198bd25432ac",
            script_pub_key0.program.hex(),
        )

        # Second key/script - P2WPKH
        key1 = ECPrivkey(
            bytes.fromhex(
                "619c335025c7f4012e556c2a58b2506e30b8511b53ade95ea316fd8c3286feb9"
            )
        )
        self.assertEqual(
            "025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee6357",
            key1.get_public_key_hex(),
        )
        script_pub_key1 = ScriptBuilder.create_p2wpkh_output_script(
            hash_160(key1.get_public_key_bytes())
        )
        self.assertEqual(
            "00141d0f172a0ecb48aee1be1f2687d2963ae33f71a1",
            script_pub_key1.program.hex(),
        )

        dummy_tx = Transaction(MAINNET)
        output = dummy_tx.add_output(
            TransactionOutput.from_coin_and_script(
                Coin.COIN().multiply(6), script_pub_key1, dummy_tx
            )
        )
        tx_in1._connect(output)

        self.assertEqual(
            "63cec688ee06a91e913875356dd4dea2f8e0f2a2659885372da2a37e32c7532e",
            tx.hash_for_signature(
                0, script_pub_key0, TransactionSigHash.ALL, False
            ).hex(),
        )

        # tx_sig0 = tx.calculate_signature(
        #     tx, 0, key0, script_pub_key0, TransactionSigHash.ALL, False
        # )
        # self.assertEqual(
        #     "30450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01",
        #     tx_sig0.encode_to_bitcoin().hex(),
        # )

        witness_script = ScriptBuilder.create_p2pkh_output_script(
            hash_160(key1.get_public_key_bytes())
        )
        self.assertEqual(
            "76a9141d0f172a0ecb48aee1be1f2687d2963ae33f71a188ac",
            witness_script.program.hex(),
        )

        self.assertEqual(
            "c37af31116d1b27caf68aae9e3ac82f1477929014d5b917657d0eb49478cb670",
            tx.hash_for_witness_signature(
                1, witness_script, tx_in1.get_value(), TransactionSigHash.ALL, False
            ).hex(),
        )
        # tx_sig1 = tx.calculate_witness_signature(
        #     tx, 1, key1, witness_script, TransactionSigHash.ALL, False
        # )
        # self.assertEqual(
        #     "304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee01",
        #     tx_sig1.encode_to_bitcoin().hex(),
        # )

        # self.assertFalse(self.correctly_spends(tx_in0, script_pub_key0, 0))
        # tx_in0.script_sig = (
        #     ScriptBuilder().data(tx_sig0.encode_to_bitcoin()).build().program
        # )
        # self.assertTrue(self.correctly_spends(tx_in0, script_pub_key0, 0))

        # self.assertFalse(self.correctly_spends(tx_in1, script_pub_key1, 1))
        # tx_in1.witness = TransactionWitness.redeem_p2wpkh(
        #     tx_sig1, key1
        # ).construct_witness()
        # self.assertTrue(self.correctly_spends(tx_in1, script_pub_key1, 1))

        # Check the final signed transaction
        # signed_tx_hex = (
        #     "01000000"  # version
        #     + "00"  # marker
        #     + "01"  # flag
        #     + "02"  # num txIn
        #     + "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f"
        #     + "00000000"
        #     + "494830450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01"
        #     + "eeffffff"  # txIn
        #     + "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a"
        #     + "01000000"
        #     + "00"
        #     + "ffffffff"  # txIn
        #     + "02"  # num txOut
        #     + "202cb20600000000"
        #     + "1976a914"
        #     + "8280b37df378db99f66f85c95a783a76ac7a6d59"
        #     + "88ac"  # txOut
        #     + "9093510d00000000"
        #     + "1976a914"
        #     + "3bde42dbee7e4dbe6a21b2d50ce2f0167faa8159"
        #     + "88ac"  # txOut
        #     + "00"  # witness (empty)
        #     + "02"  # witness (2 pushes)
        #     + "47"  # push length
        #     + "304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee01"  # push
        #     + "21"  # push length
        #     + "025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee6357"  # push
        #     + "11000000"
        # )  # nLockTime
        # self.assertEqual(signed_tx_hex, tx.bitcoin_serialize().hex())
        # self.assertEqual(len(signed_tx_hex) // 2, tx.get_message_size())

    def correctly_spends(
        self, tx_in: "TransactionInput", script_pub_key: "Script", input_index: int
    ):
        try:
            tx_in.get_script_sig().correctly_spends(
                tx_in.parent,
                input_index,
                tx_in.witness_elements,
                tx_in.get_value(),
                script_pub_key,
                Script.ALL_VERIFY_FLAGS,
            )
            return True
        except Exception:  # Replace with specific ScriptException when available
            return False


if __name__ == "__main__":
    unittest.main()
