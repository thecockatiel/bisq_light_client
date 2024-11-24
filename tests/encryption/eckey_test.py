import unittest

from bisq.common.crypto.encryption import Encryption


class EcKeyTest(unittest.TestCase):
    def setUp(self):
        # https://github.com/bisq-network/bisq/blob/v1.9.17/core/src/main/java/bisq/core/filter/FilterManager.java#L136
        # https://github.com/bisq-network/bisq/blob/master/common/src/main/java/bisq/common/app/DevEnv.java#L41
        self.dev_privileged_private_key_hex = "6ac43ea1df2a290c1c8391736aa42e4339c5cb4f110ff0257a13b63211977b7a"
        self.dev_privileged_public_key_hex = "027a381b5333a56e1cc3d90d3a7d07f26509adf7029ed06fc997c656621f8da1ee"
        
    def test_private_key_to_public_key_validation(self):
        private_key = Encryption.get_ec_private_key_from_bytes(bytes.fromhex(self.dev_privileged_private_key_hex))
        public_key_hex = Encryption.get_ec_public_key_bytes_from_private_key(private_key).hex()
        self.assertEqual(self.dev_privileged_public_key_hex, public_key_hex)


if __name__ == "__main__":
    unittest.main()
