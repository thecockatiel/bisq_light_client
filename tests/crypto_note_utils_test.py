import unittest

from bisq.asset.crypto_note_utils import MoneroBase58 
 
class CryptoNoteUtilsTest(unittest.TestCase):

    def test_compare_monero_address_prefix_with_java_result(self):
        address1 = "4BJHitCigGy6giuYsJFP26KGkTKiQDJ6HJP1pan2ir2CCV8Twc2WWmo4fu1NVXt8XLGYAkjo5cJ3yH68Lfz9ZXEUJ9MeqPW"
        address2 = "46tM15KsogEW5MiVmBn7waPF8u8ZsB6aHjJk7BAv1wvMKfWhQ2h2so5BCJ9cRakfPt5BFo452oy3K8UK6L2u2v7aJ3Nf7P2"
        address3 = "86iQTnEqQ9mXJFvBvbY3KU5do5Jh2NCkpTcZsw3TMZ6oKNJhELvAreZFQ1p8EknRRTKPp2vg9fJvy47Q4ARVChjLMuUAFQJ"
        prefix1 = 18
        prefix2 = 18
        prefix3 = 42
        self.assertEqual(MoneroBase58.decode_address(address1, True), prefix1)
        self.assertEqual(MoneroBase58.decode_address(address2, True), prefix2)
        self.assertEqual(MoneroBase58.decode_address(address3, True), prefix3)

    def test_compare_integrated_modero_address_prefix_with_java_result(self):
        address1 = "4LL9oSLmtpccfufTMvppY6JwXNouMBzSkbLYfpAV5Usx3skxNgYeYTRj5UzqtReoS44qo9mtmXCqY45DJ852K5Jv2bYXZKKQePHES9khPK"
        address2 = "4GdoN7NCTi8a5gZug7PrwZNKjvHFmKeV11L6pNJPgj5QNEHsN6eeX3DaAQFwZ1ufD4LYCZKArktt113W7QjWvQ7CWD1FFMXoYHeE6M55P9"
        address3 = "4GdoN7NCTi8a5gZug7PrwZNKjvHFmKeV11L6pNJPgj5QNEHsN6eeX3DaAQFwZ1ufD4LYCZKArktt113W7QjWvQ7CW82yHFEGvSG3NJRNtH"
        prefix1 = 19
        prefix2 = 19
        prefix3 = 19
        self.assertEqual(MoneroBase58.decode_address(address1, True), prefix1)
        self.assertEqual(MoneroBase58.decode_address(address2, True), prefix2)
        self.assertEqual(MoneroBase58.decode_address(address3, True), prefix3)
        
    def test_invalid_monero_addresses(self):
        address1 = "4BJHitCigGy6giuYsJFP26KGkTKiQDJ6HJP1pan2ir2CCV8Twc2WWmo4fu1NVXt8XLGYAkjo5cJ3yH68Lfz9ZXEUJ9MeqP"
        address2 = "4BJHitCigGy6giuYsJFP26KGkTKiQDJ6HJP1pan2ir2CCV8Twc2WWmo4fu1NVXt8XLGYAkjo5cJ3yH68Lfz9ZXEUJ9MeqPWW"
        address3 = "86iQTnEqQ9mXJFvBvbY3KU5do5Jh2NCkpTcZsw3TMZ6oKNJhELvAreZFQ1p8EknRRTKPp2vg9fJvy47Q4ARVChjLMuUAFQ!"
        address4 = "76iQTnEqQ9mXJFvBvbY3KU5do5Jh2NCkpTcZsw3TMZ6oKNJhELvAreZFQ1p8EknRRTKPp2vg9fJvy47Q4ARVChjLMuUAFQJ"
        with self.assertRaises(Exception):
            MoneroBase58.decode_address(address1, True)
        with self.assertRaises(Exception):
            MoneroBase58.decode_address(address2, True)
        with self.assertRaises(Exception):
            MoneroBase58.decode_address(address3, True)
        with self.assertRaises(Exception):
            MoneroBase58.decode_address(address4, True)


if __name__ == '__main__':
    unittest.main()