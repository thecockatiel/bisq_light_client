import unittest
from bisq.asset.coins.monero import Monero
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MoneroTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Monero())

    def test_valid_addresses(self):
        self.assert_valid_address("4BJHitCigGy6giuYsJFP26KGkTKiQDJ6HJP1pan2ir2CCV8Twc2WWmo4fu1NVXt8XLGYAkjo5cJ3yH68Lfz9ZXEUJ9MeqPW")
        self.assert_valid_address("46tM15KsogEW5MiVmBn7waPF8u8ZsB6aHjJk7BAv1wvMKfWhQ2h2so5BCJ9cRakfPt5BFo452oy3K8UK6L2u2v7aJ3Nf7P2")
        self.assert_valid_address("86iQTnEqQ9mXJFvBvbY3KU5do5Jh2NCkpTcZsw3TMZ6oKNJhELvAreZFQ1p8EknRRTKPp2vg9fJvy47Q4ARVChjLMuUAFQJ")

        # integrated addresses
        self.assert_valid_address("4LL9oSLmtpccfufTMvppY6JwXNouMBzSkbLYfpAV5Usx3skxNgYeYTRj5UzqtReoS44qo9mtmXCqY45DJ852K5Jv2bYXZKKQePHES9khPK")
        self.assert_valid_address("4GdoN7NCTi8a5gZug7PrwZNKjvHFmKeV11L6pNJPgj5QNEHsN6eeX3DaAQFwZ1ufD4LYCZKArktt113W7QjWvQ7CWD1FFMXoYHeE6M55P9")
        self.assert_valid_address("4GdoN7NCTi8a5gZug7PrwZNKjvHFmKeV11L6pNJPgj5QNEHsN6eeX3DaAQFwZ1ufD4LYCZKArktt113W7QjWvQ7CW82yHFEGvSG3NJRNtH")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("4BJHitCigGy6giuYsJFP26KGkTKiQDJ6HJP1pan2ir2CCV8Twc2WWmo4fu1NVXt8XLGYAkjo5cJ3yH68Lfz9ZXEUJ9MeqP")
        self.assert_invalid_address("4BJHitCigGy6giuYsJFP26KGkTKiQDJ6HJP1pan2ir2CCV8Twc2WWmo4fu1NVXt8XLGYAkjo5cJ3yH68Lfz9ZXEUJ9MeqPWW")
        self.assert_invalid_address("86iQTnEqQ9mXJFvBvbY3KU5do5Jh2NCkpTcZsw3TMZ6oKNJhELvAreZFQ1p8EknRRTKPp2vg9fJvy47Q4ARVChjLMuUAFQ!")
        self.assert_invalid_address("76iQTnEqQ9mXJFvBvbY3KU5do5Jh2NCkpTcZsw3TMZ6oKNJhELvAreZFQ1p8EknRRTKPp2vg9fJvy47Q4ARVChjLMuUAFQJ")

if __name__ == "__main__":
    unittest.main()
