import unittest

from bitcoinj.crypto.transaction_signature import TransactionSignature


class TransactionSignatureTest(unittest.TestCase):

    def test_transaction_signatures(self):
        sig_canonical = [
            "300602010002010001",
            "3008020200ff020200ff01",
            "304402203932c892e2e550f3af8ee4ce9c215a87f9bb831dcac87b2838e2c2eaa891df0c022030b61dd36543125d56b9f9f3a1f9353189e5af33cdda8d77a5209aec03978fa001",
            "30450220076045be6f9eca28ff1ec606b833d0b87e70b2a630f5e3a496b110967a40f90a0221008fffd599910eefe00bc803c688c2eca1d2ba7f6b180620eaa03488e6585db6ba01",
            "3046022100876045be6f9eca28ff1ec606b833d0b87e70b2a630f5e3a496b110967a40f90a0221008fffd599910eefe00bc803c688c2eca1d2ba7f6b180620eaa03488e6585db6ba01",
        ]

        sig_non_canonical = [
            "non-hex strings are ignored",
            "too short:",
            "30050201FF020001",
            "too long:",
            "30470221005990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba6105022200002d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "hashtype:",
            "304402205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed11",
            "type:",
            "314402205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "total length:",
            "304502205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "S len oob:",
            "301F01205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb101",
            "R+S:",
            "304502205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed0001",
            "R type:",
            "304401205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "R len = 0:",
            "3024020002202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "R<0:",
            "304402208990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "R padded:",
            "30450221005990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610502202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "S type:",
            "304402205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba610501202d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "S len = 0:",
            "302402205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba6105020001",
            "S<0:",
            "304402205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba61050220fd5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
            "S padded:",
            "304502205990e0584b2b238e1dfaad8d6ed69ecc1a4a13ac85fc0b31d0df395eb1ba61050221002d5876262c288beb511d061691bf26777344b702b00f8fe28621fe4e566695ed01",
        ]

        for sig in sig_canonical:
            self.assertTrue(
                TransactionSignature.is_encoding_canonical(bytes.fromhex(sig))
            )

        for sig in sig_non_canonical:
            try:
                self.assertFalse(
                    TransactionSignature.is_encoding_canonical(bytes.fromhex(sig))
                )
            except ValueError as e:
                # Expected for non-hex strings in the JSON that we should ignore
                if "non-hexadecimal" not in str(e):
                    raise e

if __name__ == "__main__":
    unittest.main()
