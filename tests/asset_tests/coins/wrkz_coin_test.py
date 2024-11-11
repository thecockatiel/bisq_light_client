import unittest
from bisq.asset.coins.wrkz_coin import WrkzCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class WrkzCoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, WrkzCoin())

    def test_valid_addresses(self):
        self.assert_valid_address("WrkzjsomAAfH8kotfaTyVYfya7PNQt2oL4regF1VpTV9TSezdyxcQpRW2jGptwPP6zLgQUa7Lem1dBWfGM7LfJqs719UZhX9Hg")
        self.assert_valid_address("WrkzpRgV26G8p8FUfFzaYbd15Nmq3SsRSVbG8yPjvt4W4D5KBHTV2RHbzQVE1TAt1NV21Tp6xiFATJT8QXoxeEUQ8DPY1Zkjnf")
        self.assert_valid_address("WrkzmetNqgJG5SwtaVhyTxijdx6JGtUeHELTpwfgC9Ym1Ps4JdQtanXLK8Xk5TeMUTEbsmDJ8taXYiyYZpPHSg5X1wC8ij7fdG")

    def test_invalid_addresses(self):
        self.assert_invalid_address("WrkzQokcStLUSALE5Ra17v2n6ad65h8wL5vqABKkoWy7Xicz9znqPSgS2MRVkuYtRAaJiMFuyDCFF1oJgT7PHb8i9yM")
        self.assert_invalid_address("WrkskixT63cYzLFmDoA5WN7RbihYBwbzJJmjR9zgjD3ZUotbFGBgv1RaUAu1fWWT4QeEEktQfZK9AFPh19t2U8uG49EH3WSVEn")
        self.assert_invalid_address("")
        self.assert_invalid_address("WrkzUAxg9TSdkh6tfh5pk84XgKeyNe8T4TvaSgk87kk6iCUEitkk2sk6wVtKJXk5BM3kwh2ftnkaVfBWfBPr8igZ2xkn#RoUxF")
        self.assert_invalid_address("WrkzXTU4REbRijuLPpds2k4BhcBGgXFpeEaXKs49D7$PFuqBYpQw2tQbAApoQLAp2iWVsoxiPmcERXhHrhtCLnzL4ezB8kAbxH")
        self.assert_invalid_address("cccd2bd37455350e7586cf9315c7f3acd3de56321aa356ff3391bd21f0bbf502")


if __name__ == "__main__":
    unittest.main()
