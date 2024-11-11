import unittest
from bisq.asset.coins.mile import Mile
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MileTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Mile())

    def test_valid_addresses(self):
        self.assert_valid_address("2WeY8JpRJgrvWQxbSPuyhsBMjtZMMN7cADEomPHh2bCkdZ7xQW")
        self.assert_valid_address("NTvSfK1Gr5Jg97UvJo2wvi7BTZo8KqJzgSL2FCGucF6nUH7yq")
        self.assert_valid_address("ztNdPsuyfDWt1ufCbDqaCDQH3FXvucXNZqVrdzsWvzDHPrkSh")
        self.assert_valid_address("jkvx3z98rJmuVKqMSktDpKTSBrsqJEtTBW1CBSWJEtchDGkDX")
        self.assert_valid_address("is2YXBxk91d4Lw4Pet7RoP8KAxCKFHUC6iQyaNgmac5ies6ko")
        self.assert_valid_address("2NNEr5YLniGxWajoeXiiAZPR68hJXncnhEmC4GWAaV5kwaLRcP")
        self.assert_valid_address("wGmjgRu8hgjgRsRV8k6h2puis1K9UQCTKWZEPa4yS8mrmJUpU")
        self.assert_valid_address("i8rc9oMunRtVbSxA4VBESxbYzHnfhP39aM5M1srtxVZ8oBiKD")
        self.assert_valid_address("vP4w8khXHFQ7cJ2BJNyPbJiV5kFfBHPVivHxKf5nyd8cEgB9U")
        self.assert_valid_address("QQQZZa46QJ3499RL8CatuqaUx4haKQGUuZ4ZE5SeL13Awkf6m")
        self.assert_valid_address("qqqfpHD3VbbyZXTHgCW2VX8jvoERcxanzQkCqVyHB8fRBszMn")
        self.assert_valid_address("BiSQkPqCCET4UovJASnnU1Hk5bnqBxBVi5bjA5wLZpN9HCA6A")
        self.assert_valid_address("bisqFm6Zbf6ULcpJqQ2ibn2adkL2E9iivQFTAP15Q18daQxnS")
        self.assert_valid_address("miLEgbhGv4ARoPG2kAhTCy8UGqBcFbsY6rr5tXq63nH8RyqcE")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1WeY8JpRJgrvWQxbSPuyhsBMjtZMMN7cADEomPHh2bCkdZ7xQW")
        self.assert_invalid_address("2WeY8JpRJgrvWQxbSPuyhsBMjtZMMN3cADEomPHh2bCkdZ7xQW")
        self.assert_invalid_address("2WeY8JpRJgrvWQxbSPuyhsBMjtZMMN7cADEomPHh2bCkdZ7xQ1")
        self.assert_invalid_address("2WeY8JpRJgrvWQxbSPuyhsBMjtZMMN7cADEomPHh2bCkdZ7xQ")
        self.assert_invalid_address("WeY8JpRJgrvWQxbSPuyhsBMjtZMMN7cADEomPHh2bCkdZ7xQW")
        self.assert_invalid_address("2WeY8JpRJgrvWQx")
        self.assert_invalid_address("2WeY8JpRJgrvWQxbSPuyhsBMjtZMMN7cADEomPHh2bCkdZ7xQW1")
        self.assert_invalid_address("milEgbhGv4ARoPG2kAhTCy8UGqBcFbsY6rr5tXq63nH8RyqcE")
        self.assert_invalid_address("miLegbhGv4ARoPG2kAhTCy8UGqBcFbsY6rr5tXq63nH8RyqcE")
        self.assert_invalid_address("1111111")

if __name__ == "__main__":
    unittest.main()
