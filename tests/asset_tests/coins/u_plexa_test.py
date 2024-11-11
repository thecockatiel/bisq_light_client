import unittest
from bisq.asset.coins.u_plexa import uPlexa
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class uPlexaTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, uPlexa())

    def test_valid_addresses(self):
        self.assert_valid_address("UPX1dz81hmfWc7AUhn16JATXJJgZeQZ4zLKA4tnHJHcdS5zoSaKQUoaGqDUQnTXecPL4mjJF1vkwRF3EEq5UJdSw8A84sXDjFP")
        self.assert_valid_address("UPi1S1uqRRNSgC26PjasZP8FwTBRwnAEmBnx5mAYsbGqRvsU46aficYEA3FAT621EuPeChyKQumS7j6jpF74zW9tLJMve8kUJLP5zUgR5ts8W")
        self.assert_valid_address("UmV7QTQs5Q47wMPggtuQSMTvuqNie1MRmbD4AG1xJXykZmxBG4P18p4CHqkV5sKDRXauXWbs76835PZoemQmPGJC1Dv2zdF43")
        self.assert_valid_address("UmWh1MthnAiRP4GuN3DEQxPt6kgeAZfJLUuX1krtufAj2XvUJxDYnuYTAQzEp25V2W8BAJQkfXj8yFNUqQphxddN35nRLnZeE")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("UPXLsinT9duNEtHGqAUicJKD2cmGiB9gB6sqHqWvV6suB4TtPSR8ynyh2vVVvNyDE6g7WEaBxCG8GD1KM2ffWPx7FLXgeJbNYrp")
        self.assert_invalid_address("UPXsjCoYrxag2pPoDDTB4cRriKCNn8WjhY99kqjYuNdTfE4MU2Yo1CPdpyK7PXpxDcAd5YDNerE6WCc4cVQvEbxLaHk4UcvbRp2")
        self.assert_invalid_address("UPXsinT9duNEtHGqAUicJKD2cmGiB9gB6sqHqWvV6suBx4TtPSR8ynyh2vVVvNyDE6g7W!!!xCG8GD1KM2ffWP7FLXgeJbNYrp2")
        self.assert_invalid_address("UmVSrJ7ES1IIIIIGHFm69SU6dTTKt8Vi6V7BoC3wsLccd1Y2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTP")
        self.assert_invalid_address("UmWrJ7ES1wGsikGHFm69SU6dTTKt8Vi6V7BoC3wsLcc1xY2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTPe")
        self.assert_invalid_address("UPi12rJ7ES1wGsikGHFm69SU6dTTKt8Vi6V7BoC36sqHqWvwsLcc1Y2CXgQkW7vHSe5uArGU9TjUC5RtvzhCycVDnPPbThTmZA8VqDzTPeM1")
        self.assert_invalid_address("UPisBB18NdcSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93vd6DEu3PcSywKDshsywbjc5uCi8ybSUtWgvM3LfzaYe93d96NjjvBCYU2SZD2of")

if __name__ == "__main__":
    unittest.main()
