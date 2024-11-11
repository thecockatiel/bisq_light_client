import unittest
from bisq.asset.coins.solo import Solo
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class SoloTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Solo())

    def test_valid_addresses(self):
        self.assert_valid_address("SL3UVNhEHuaWK9PwhVgMZWD5yaL6VBC4xRuXLnLFWizxavKvSqbcSpH2fG3dT36uMJEQ6XoKBqvFLUnzWG4Rb5e11yqsioFy8")
        self.assert_valid_address("Ssy27ePzscCj4spPjgtc8NKGSud9eLFLHGEWNAo8PuC53NnWhDDTX17Cfo3BzFKdYZfU9ovtEYNtQ4ezTtPhAHEuAR5mF8dTqB")
        self.assert_valid_address("Ssy2WFFnmi3XYJz8UsXPKzHtUxFdVhdSuU3sBGmpTbTLQqpZEMPS8GB486Q8UCaskdbGzxJxwdJYobtJmEPwDawa5mXD5spNbs")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("SL3dqGkkFszKzjzyXSLkYB6X9uqad7ih3DJtTeB8hrzD9iaRjWAUHZ8FA3NErphWM00NzURSTL7FEZ9un9fgLYjK2f7mHRFBn")
        self.assert_invalid_address("Ssy2WLjegYxS5P1djMSRmVG8EzXDfHyde6BiZRd3aDyVh1vjwUB2GJHfWhVsvg1i4TjWyGRC9rD4n3kCE2gPA9yx6K34AyzcMZ")
        self.assert_invalid_address("Sl3UVNhEHuaWK9PwhVgMZWD5yaL6VBC4xRuXLnLFWizxavKvSXxXSpam8d3dMaDuMJEQ6XoKBqvFLUnzWG4Rb5e11yqsioFy8")
        self.assert_invalid_address("Ssy2WFFnmi3XYJz8UsXPKzHtUxFdVhdSuU3sBGmpTbTLQLoLIghGooDdf6QTryaskdbGzxJxwdJYobtJmEPwDawa5mXD5spNbs")

if __name__ == "__main__":
    unittest.main()
