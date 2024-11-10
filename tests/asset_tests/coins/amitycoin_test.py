import unittest
from bisq.asset.coins.amitycoin import Amitycoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class AmitycoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Amitycoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("amitMgDfvfUZ2CP1g1SEJQSN4n7qK4d45hqXSDtiFMwE5uo7DnSihknJzcEG9WtFc26fnhDHK6ydjBDKe6wjCoGt4RiP18a5Zb")
        self.assert_valid_address("amitUnFFwApLG9btiPWRgTjRCQUj9kZjQJ8kH3ZraSsCU4yzX4AzgaoP8jkgXhp5c5jQT3idFJChAPYzA2EydJ5A4bShqrEixa")
        self.assert_valid_address("amitAcVJTUZKJtYYsosMXJBQeEbt3ZV9qSvoQ1EqkvA45MRUaYWECYNKyRZ82BvLM9MPD2Gpud3DbGzGsStKnZ9x5yKVPVGJUa")

    def test_invalid_addresses(self):
        self.assert_invalid_address("amitAcVJTUZKJtYYsosMXJBQeEbt3ZV9qSvoQ1EqkvA45MRUaYWECYNKyRZ82BvLM9MPD2Gpud3DbGzGsStKnZ9")
        self.assert_invalid_address("amitAcVJTUZKJtYYsosMXJBQeEbt3ZV9qSvoQ1EqkvA45MRUaYWECYNKyRZ82BvLM9MPD2Gpud3DbGzGsStKnZ9x5yKVPVGJUaljashfeafh")
        self.assert_invalid_address("")
        self.assert_invalid_address("amitAcVJTUZKJtYYsosMXJBQeEbt3ZV9qSvoQ1EqkvA45MRUaYWECY#RoPOWRwpsx1F")
        self.assert_invalid_address("amitAcVJTUZKJtYYsosMXJByRZ82BvLM9MPD2Gpud3DbGzGsStKnZ9x5yKVPVGJUaJbc2q4C4fWN$C4fWNLoDLDvADvpjNYdt3sdRB434UidKXimQQn")
        self.assert_invalid_address("dsfkjasd56yaSDdguaw")
        self.assert_invalid_address("KEKlulzlksadfwe")
        self.assert_invalid_address("HOleeSheetdsdjqwqwpoo3")


if __name__ == '__main__':
    unittest.main()