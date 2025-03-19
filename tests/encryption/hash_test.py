import unittest
from bisq.common.crypto.hash import (
    get_keccak1600_hash,
    get_sha256_hash,
    get_sha256_hash_from_integer,
    get_sha256_ripemd160_hash,
    get_ripemd160_hash,
)


class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.str_message = "hello"
        self.int_message = 1234
        # hex values are from calling java code from bisq's Hash.java with above messages
        self.sha256_str_hex = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" 
        self.sha256_bytes_hex = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.sha256_int_hex = "4686c8f8f736985cc7c2a64066cda0e168717f7ee0ae5b425eac52d538dcd614"
        self.sha256_ripemd160_hex = "b6a9c8c230722b7c748331a8b450f05566dc7d0f"
        self.ripemd160_hex = "108f07b8382412612c048d07d13f814118445acd"
        # created from running CryptoNoteUtils.Keccak.keccak1600 on "hello"
        self.keccak1600_hex = "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"

    def test_sha256_str(self):
        self.assertEqual(get_sha256_hash(self.str_message).hex(), self.sha256_str_hex)
    
    def test_sha256_bytes(self):
        self.assertEqual(get_sha256_hash(self.str_message.encode()).hex(), self.sha256_bytes_hex)
        
    def test_sha256_int(self):
        self.assertEqual(get_sha256_hash_from_integer(self.int_message).hex(), self.sha256_int_hex)
        
    def test_sha256_ripemd160(self):
        self.assertEqual(get_sha256_ripemd160_hash(self.str_message.encode()).hex(), self.sha256_ripemd160_hex)
        
    def test_ripemd160(self):
        self.assertEqual(get_ripemd160_hash(self.str_message.encode()).hex(), self.ripemd160_hex)
        
    def test_keccak1600(self):
        self.assertEqual(get_keccak1600_hash(self.str_message.encode()).hex(), self.keccak1600_hex)


if __name__ == "__main__":
    unittest.main()
