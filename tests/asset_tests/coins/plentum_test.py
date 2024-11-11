import unittest
from bisq.asset.coins.plentum import Plenteum 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class PlenteumTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Plenteum())
    
    def test_valid_addresses(self):
        self.assert_valid_address("PLeah9bvqxEDUWbRFqgNcYDeoL772WH9mcCQu9p29MC23NeCUkbVdUEfwDAtF8SgV81kf2hwCdpxqAJmC9k3nJsA7W4UThrufj")
        self.assert_valid_address("PLeavHTKHz9UcTCSCmd8eihuLxbsK9a7wSpfcYXPYY87JMpvYwwTH6Df32fRLc1r4rQMKoDLpTvywXx4FUVTggCR4jh9PEhvXb")
        self.assert_valid_address("PLeazd7iQEoFWJttR6353BMvs1cJfMqDmEUk2Z2XSoDdZigY5CbNLvrFUr7duvnEFdSKRdCQYTDkrcySYD1zaFtT9YMubRjHL2")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("PLev23ymatPTWgN1jncG33hMdJxZBLrBcCWQBGGGC14CFMUCq1nvxiV8d5cW92mmavzw542bpyjYXd8")
        self.assert_invalid_address("PLeuxauCnCH7XZrSZSZw7XEEbkgrnZcaE1MK8wLtTYkF3g1J7nciYiaZDsTNYm2oDLTAM2JPq4rrlhVN5cXWpTPYh8P5wKbXNdoh")
        self.assert_invalid_address("")
        self.assert_invalid_address("PLev3xxpAFfXKwF5ond4sWDX3ATpZngT88KpPCCJKcuRjGktgp5HHTK2yV7NTo8687u5jwMigLmHaoFKho0OhVmF8WP9pVZhBL9kC#RoPOWRwpsx1F")
        self.assert_invalid_address("PLeuwafXHTPzj1d2wc7c9X69r3qG1277ecnLnUaZ61M1YV5d3GYAs1Jbc2q4C4fWN$C4fWNLoDLDvADvpjNYdt3sdRB434UidKXimQQn")
        self.assert_invalid_address("1jRo3rcp9fjdfjdSGpx")
        self.assert_invalid_address("GDARp92UtmTWDjZatG8sduRockSteadyWasHere3atrHSXr9vJzjHq2TfPrjateDz9Wc8ZJKuDayqJ$%")
        self.assert_invalid_address("F3xQ8Gv6xnvDhUrM57z71bfFvu9HeofXtXpZRLnrCN2s2cKvkQowrWjJTGz4676ymKvU4NzYT5Aadgsdhsdfhg4gfJwL2yhhkJ7")


if __name__ == '__main__':
    unittest.main()