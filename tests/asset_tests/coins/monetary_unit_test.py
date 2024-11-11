import unittest
from bisq.asset.coins.monetary_unit import MonetaryUnit
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MonetaryUnitTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, MonetaryUnit())

    def test_valid_addresses(self):
        self.assert_valid_address("7VjG4Vjnu488k14QdpxswKk1acVgySqV6c")
        self.assert_valid_address("7U42XyYEf7CsLsaq84mRxMaMfst7f3r4By")
        self.assert_valid_address("7hbLQSY9SnyHf1RwiTniMt8vT94x7pqJEr")
        self.assert_valid_address("7oM4HbCStpDQ8imocHPVjNWGVj9gg54erh")
        self.assert_valid_address("7SUheC6Xp12G9CCgoMJ2dT8e9zwnFRwjrU")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0U42XyYEf7CsLsaq84mRxMaMfst7f3r4By")
        self.assert_invalid_address("#7VjG4Vjnu488k14QdpxswKk1acVgySqV6c")
        self.assert_invalid_address("7SUheC6Xp12G9CCgoMJ2dT8e9zwnFRwjr")
        self.assert_invalid_address("7AUheX6X")

if __name__ == "__main__":
    unittest.main()
