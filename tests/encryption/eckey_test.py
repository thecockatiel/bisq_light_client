import unittest

from bisq.common.crypto.encryption import Encryption, ECPubkey, ECPrivkey


class EcKeyTest(unittest.TestCase):
    def setUp(self):
        # https://github.com/bisq-network/bisq/blob/v1.9.17/core/src/main/java/bisq/core/filter/FilterManager.java#L136
        # https://github.com/bisq-network/bisq/blob/master/common/src/main/java/bisq/common/app/DevEnv.java#L41
        self.dev_privileged_private_key_hex = "6ac43ea1df2a290c1c8391736aa42e4339c5cb4f110ff0257a13b63211977b7a"
        self.dev_privileged_public_key_hex = "027a381b5333a56e1cc3d90d3a7d07f26509adf7029ed06fc997c656621f8da1ee"
        self.ZERO_HASH_BYTES = bytes(32)
        
    def test_private_key_to_public_key_validation(self):
        private_key = Encryption.get_ec_private_key_from_int_hex_string(self.dev_privileged_private_key_hex)
        public_key_hex = private_key.get_public_key_hex()
        self.assertEqual(self.dev_privileged_public_key_hex, public_key_hex)

    def test_eckey(self):
        privkey = Encryption.get_ec_private_key_from_int_hex_string("180cb41c7c600be951b5d3d0a7334acc7506173875834f7a6c4c786a28fcbb19")
        output_signature = privkey.sign(self.ZERO_HASH_BYTES)
        self.assertTrue(privkey.verify_message_hash(output_signature, self.ZERO_HASH_BYTES))
        another_signature = bytes.fromhex("3045022100cfd454a1215fdea463201a7a32c146c1cec54b60b12d47e118a2add41366cec602203e7875d23cc80f958e45298bb8369d4422acfbc1c317353eebe02c89206b3e73")
        self.assertTrue(privkey.verify_message_hash(another_signature, self.ZERO_HASH_BYTES))
        
        java_signature = bytes.fromhex("3046022100dffbc26774fc841bbe1c1362fd643609c6e42dcb274763476d87af2c0597e89e022100c59e3c13b96b316cae9fa0ab0260612c7a133a6fe2b3445b6bf80b3123bf274d")
        self.assertTrue(privkey.verify_message_hash(java_signature, self.ZERO_HASH_BYTES))
        
    def test_eckey_pubkey_import(self):
        pubkey = Encryption.get_ec_public_key_from_bytes(bytes.fromhex("0358d47858acdc41910325fce266571540681ef83a0d6fedce312bef9810793a27"))
        self.assertTrue(pubkey)
        
    def test_eckey_pubkey_export(self):
        pubkey = Encryption.get_ec_public_key_from_bytes(bytes.fromhex("0358d47858acdc41910325fce266571540681ef83a0d6fedce312bef9810793a27"))
        exported = pubkey.get_public_key_hex()
        self.assertEqual("0358d47858acdc41910325fce266571540681ef83a0d6fedce312bef9810793a27", exported)
    
    def test_is_pubkeys_equal(self):
        pubkey1 = Encryption.get_ec_public_key_from_bytes(bytes.fromhex("0358d47858acdc41910325fce266571540681ef83a0d6fedce312bef9810793a27"))
        pubkey2 = Encryption.get_ec_public_key_from_bytes(bytes.fromhex("0358d47858acdc41910325fce266571540681ef83a0d6fedce312bef9810793a27"))
        self.assertTrue(pubkey1 == pubkey2) # for later detection if it supports __eq__ method
        self.assertTrue(Encryption.is_pubkeys_equal(pubkey1, pubkey2))
        
if __name__ == "__main__":
    unittest.main()
