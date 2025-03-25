import unittest
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.core.transaction_witness import TransactionWitness
from bitcoinj.crypto.transaction_signature import TransactionSignature
from bitcoinj.script.script import Script


class TransactionWitnessTest(unittest.TestCase):

    def test_to_string(self):
        w1 = TransactionWitness.EMPTY
        self.assertEqual("", str(w1))

        # Test witness with empty pushes
        w2 = TransactionWitness(2)
        w2.set_push(0, bytes())
        w2.set_push(1, bytes())
        self.assertEqual("EMPTY EMPTY", str(w2))

        # Test witness with mix of data and empty pushes
        w3 = TransactionWitness(4)
        w3.set_push(0, bytes.fromhex("123aaa"))
        w3.set_push(1, bytes.fromhex("123bbb"))
        w3.set_push(2, bytes())
        w3.set_push(3, bytes.fromhex("123ccc"))
        self.assertEqual("123aaa 123bbb EMPTY 123ccc", str(w3))

    def test_redeem_p2wsh(self):

        # Create signatures
        signature1 = TransactionSignature.decode_from_der(
            bytes.fromhex(
                "3045022100c3d84f7bf41c7eda3b23bbbccebde842a451c1a0aca39df706a3ff2fe78b1e0a02206e2e3c23559798b02302ad6fa5ddbbe87af5cc7d3b9f86b88588253770ab9f79"
            ),
            TransactionSigHash.ALL,
            False,
        )

        signature2 = TransactionSignature.decode_from_der(
            bytes.fromhex(
                "3045022100fcfe4a58f2878047ef7c5889fc52a3816ad2dd218807daa3c3eafd4841ffac4d022073454df7e212742f0fee20416b418a2c1340a33eebed5583d19a61088b112832"
            ),
            TransactionSigHash.ALL,
            False,
        )

        # Create witness script
        witness_script = Script(
            bytes.fromhex(
                "522102bb65b325a986c5b15bd75e0d81cf149219597617a70995efedec6309b4600fa02103c54f073f5db9f68915019801435058c9232cb72c6528a2ca15af48eb74ca8b9a52ae"
            )
        )

        # Create transaction witness
        witness = TransactionWitness.redeem_p2wsh(
            witness_script, signature1, signature2
        )

        # Assert results
        self.assertEqual(4, witness.get_push_count())
        self.assertEqual(bytes(), witness.get_push(0))
        self.assertEqual(signature1.encode_to_bitcoin(), witness.get_push(1))
        self.assertEqual(signature2.encode_to_bitcoin(), witness.get_push(2))
        self.assertEqual(witness_script.program, witness.get_push(3))

    

if __name__ == "__main__":
    unittest.main()
