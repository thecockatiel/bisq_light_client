import unittest
from bisq.asset.coins.turtle_coin import TurtleCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class TurtleCoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, TurtleCoin())

    def test_valid_addresses(self):
        self.assert_valid_address("TRTLv2X775FNQmN8x2UC3TVzs6trRHwUAcQSL6RUyRXR6JjwFYP8XG8VTCsi7QgPcWBJUWJk2SwaMYvrMk37T4nFVLPigMXcsf8")
        self.assert_valid_address("TRTLuyTzuoDL9wvoq9VcyGW9Vrp2R3161V3hSa8nZUxAL4iqbTJfFhSXpsrQunXuCGAnA72cZgYGmP7a8zJ6RrwAf5rKjwhUEU8")
        self.assert_valid_address("TRTLv2YGSbTgmAkZDYvRM8X6bLcJXYr4qMDTXYth9ppc2rHfnNGXPcbBTWxfRxwPTnJvFX1txGh6j9tQ9spJs3US3WwvDzkGsXC")

    def test_invalid_addresses(self):
        self.assert_invalid_address("TRTLv23ymatPTWgN1jncG33hMdJxZBLrBcCWQBGGGC14CFMUCq1nvxiV8d5cW92mmavzw542bpyjYXd8")
        self.assert_invalid_address("TRLuxauCnCH7XZrSZSZw7XEEbkgrnZcaE1MK8wLtTYkF3g1J7nciYiaZDsTNYm2oDLTAM2JPq4rrlhVN5cXWpTPYh8P5wKbXNdoh")
        self.assert_invalid_address("")
        self.assert_invalid_address("TRTLv3xxpAFfXKwF5ond4sWDX3AVgZngT88KpPCCJKcuRjGktgp5HHTK2yV7NTo8659u5jwMigLmHaoFKho0OhVmF8WP9pVZhBL9kC#RoUKWRwpsx1F")
        self.assert_invalid_address("TRTLuwafXHTPzj1d2wc7c9X69r3qG1277ecnLnUaZ61M1YV5d3GYAs1Jbc2q4C4fWN$C4fWNLoDLDvADvpjNYdt3sdRB434UidKXimQQn")
        self.assert_invalid_address("1jRo3rcp9fjdfjdSGpx")
        self.assert_invalid_address("GDARp92UtmTWDjZatG8sduRockSteadyWasHere3atrHSXr9vJzjHq2TfPrjateDz9Wc8ZJKuDayqJ$%")
        self.assert_invalid_address("F3xQ8Gv6xnvDhUrM57z71bfFvu9HeofXtXpZRLnrCN2s2cKvkQowrWjJTGz4676ymKvU4NzPY8Cadgsdhsdfhg4gfJwL2yhhkJ7")

if __name__ == "__main__":
    unittest.main()
