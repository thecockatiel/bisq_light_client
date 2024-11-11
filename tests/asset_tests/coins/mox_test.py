import unittest
from bisq.asset.coins.mox import MoX
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MoXTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, MoX())

    def test_valid_addresses(self):
        self.assert_valid_address("XwoHEJVYYZEBXB99yPP1AWNYYTDLPGHZ11jTia4RWRpwbohuChbpPngF42RCoaKaJciCmhwdKWsBBQPt8Ci5dr9p3BejTRxXV")
        self.assert_valid_address("XwoG8c8N8VZQy9usuHj88DK5DsezY5YrkZoSCEKg8sFfhKLhFV2NwVMPFNogZkjpPw1RiV16JQ1Mg6ygYpntKADJ2kSRv21Lc")
        self.assert_valid_address("XwoABgJx6dt96eihXdGwj31AKqsN7dTbb1vMshfmj87YRYxmieBh8zHY26AYnwDE9Ce4Mg4eB4huEHYM26bEWrN72xa6zBf17")

    def test_invalid_addresses(self):
        self.assert_invalid_address("XwoHEJVYYZEBXB99yPP1AWNYYTDLPGHZ11jTia4RWRpwbohuChbpPngF42RCoaKaJciCmhwdKWsBBQPt8Ci5dr9p3BejTRxX")
        self.assert_invalid_address("XwoHEJVYYZEBXB99yPP1AWNYYTDLPGHZ11jTia4RWRpwbohuChbpPngF42RCoaKaJciCmhwdKWsBBQPt8Ci5dr9p3BejTRxXVV")
        self.assert_invalid_address("woHEJVYYZEBXB99yPP1AWNYYTDLPGHZ11jTia4RWRpwbohuChbpPngF42RCoaKaJciCmhwdKWsBBQPt8Ci5dr9p3BejTRxXVV")
        self.assert_invalid_address("Xizx2PdSDC6B4xwcxr6ZsHAiShnj7XcXSEmf4GQRTmpDFum1MyohsekDvRQpN4eQwyZyCw4Hs2UKyJSygXwA2QhyGcS5NRVsYrM9t2SCPsxzT")
        self.assert_invalid_address("")
        self.assert_invalid_address("XwoHEJVYYZEBXB99yPP1AWNYYTDLPGHZ11jTia4RWRpwbohuChbpPngF42RCoaKaJciCmhwdKWsBBQPt8Ci5dr9p3BejTRxXV#aFejf")
        self.assert_invalid_address("1jRo3rcp9fjdfjdSGpx")
        self.assert_invalid_address("GDARp92UtmTWDjZatG8sdurzouheiuRRRTbbRtbr3atrHSXr9vJzjHq2TfPrjateDz9Wc8ZJKuDayqJ$%")
        self.assert_invalid_address("F3xQ8Gv6xnvDhUrM57z71bfFvu9HeofXtXpZRLnrCN2s2cKvkQowrWjJTGz4676ymKvU4NzPY8Cadgsdhsdfhg4gfJwL2yhhkJ7")

if __name__ == "__main__":
    unittest.main()
