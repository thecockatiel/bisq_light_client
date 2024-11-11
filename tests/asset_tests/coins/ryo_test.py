import unittest
from bisq.asset.coins.ryo import Ryo
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class RyoTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Ryo())

    def test_valid_addresses(self):
        self.assert_valid_address("RYoLsinT9duNEtHGqAUicJKD2cmGiB9gB6sqHqWvV6suB4TtPSR8ynyh2vVVvNyDE6g7WEaBxCG8GD1KM2ffWP7FLXgeJbNYrp2")
        self.assert_valid_address("RYoSrJ7ES1wGsikGHFm69SU6dTTKt8Vi6V7BoC3wsLcc1Y2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTPeM")
        self.assert_valid_address("RYoKst8YBCucSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d4qqpsJ")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("RYoLsinT9duNEtHGqAUicJKD2cmGiB9gB6sqHqWvV6suB4TtPSR8ynyh2vVVvNyDE6g7WEaBxCG8GD1KM2ffWP7FLXgeJbNYrp")
        self.assert_invalid_address("RYoLsjCoYrxag2pPoDDTB4cRriKCNn8WjhY99kqjYuNTfE4MU2Yo1CPdpyK7PXpxDcAd5YDNerE6WCc4cVQvEbxLaHk4UcvbRp23")
        self.assert_invalid_address("RYoLsinT9duNEtHGqAUicJKD2cmGiB9gB6sqHqWvV6suB4TtPSR8ynyh2vVVvNyDE6g7W!!!xCG8GD1KM2ffWP7FLXgeJbNYrp2")
        self.assert_invalid_address("RYoSrJ7ES1IIIIIGHFm69SU6dTTKt8Vi6V7BoC3wsLcc1Y2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTPeM")
        self.assert_invalid_address("RYoSrJ7ES1wGsikGHFm69SU6dTTKt8Vi6V7BoC3wsLcc1Y2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTPe")
        self.assert_invalid_address("RYoSrJ7ES1wGsikGHFm69SU6dTTKt8Vi6V7BoC3wsLcc1Y2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTPeM1")
        self.assert_invalid_address("RYoNsBB18NdcSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d6DEu3PcSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d96NjjvBCYU2SZD2of")
        self.assert_invalid_address("RYoKst8YBCucSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d4qqpsJC")
        self.assert_invalid_address("RYoKst8YBCucSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d4qqps")
        self.assert_invalid_address("RYost8YBCucSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d4qqpsJ")


if __name__ == "__main__":
    unittest.main()
