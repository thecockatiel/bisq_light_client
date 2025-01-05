import unittest

from bisq.core.xmr.knaccc.monero.crypto.crypto_util import CryptoUtil

class TestCryptoUtilTest(unittest.TestCase):
    
    def test_wallet_address(self):
        tx_key = "6c336e52ed537676968ee319af6983c80b869ca6a732b5962c02748b486f8f0f"
        self.assertEqual(tx_key, CryptoUtil.to_canoninal_tx_key(tx_key))
        self.assertEqual(tx_key, CryptoUtil.to_canoninal_tx_key(tx_key.upper()))
        
        # key with 1 above l value (created with HexEncoder.getString(ensure32BytesAndConvertToLittleEndian(l.add(BigInteger.ONE).toByteArray())))
        tx_key = "eed3f55c1a631258d69cf7a2def9de1400000000000000000000000000000010"
        self.assertNotEqual(tx_key, CryptoUtil.to_canoninal_tx_key(tx_key))

if __name__ == '__main__':
    unittest.main()