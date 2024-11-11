import unittest

from bisq.asset.coins.grin import Grin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class GrinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Grin())
    
    def test_valid_addresses(self):
        # valid slatepack addresses
        self.assert_valid_address("grin1ephxt0u33rz9zpl7exer2awfr9s9ae28qsx7908q2zq03uv3sj7suqdule")
        self.assert_valid_address("grin1wwg5k80qje0lw32ldttgl52lew0ucmv64zux27pzanl0a2ku85ps5gxafa")
        self.assert_valid_address("grin1mdxxaz8g5zc4fhqcvcu79c0sp3md9j2f6tt5cxde78scjatkh3zqzrgl9r")
        self.assert_valid_address("grin17whxsfzj3su0rtpd3hkcjt3hlatvc89dpc9syvrmq2shhnhc9f6sehqe3x")
        self.assert_valid_address("grin1cq636ment795xn68knzu0ewp73f3zdlgv6dsqv8x7vf2v0j4ek5sk6nmk3")
        self.assert_valid_address("grin1wm78wjsf2ws507hea4zqrcywxltjwhtgfrwzhdrr9l80l7tpz5fsj58lk0")
        self.assert_valid_address("grin1jezf3lkcexvj3ydjwanan6khs42fr4036guh0c4vkc04fyxarl6svjzuuh")

    def test_invalid_addresses(self):
        # invalid slatepack address (bech32 format invalid)
        self.assert_invalid_address("grin1p4fuklglxqsgg602hu4c4jl4aunu5tynyf4lkg96ezh3jefzpy6swshp5x")  # from 0015-slatepack.md#slatepackaddress

        # grinbox
        self.assert_invalid_address("gVvk7rLBg3r3qoWYL3VsREnBbooT7nynxx5HtDvUWCJUaNCnddvY")
        self.assert_invalid_address("grinbox:#gVtWzX5NTLCBkyNV19QVdnLXue13heAVRD36sfkGD6xpqy7k7e4a")
        self.assert_invalid_address("gVw9TWimGFXRjoDXWhWxeNQbu84ZpLkvnenkKvA5aJeDo31eM5tC@somerelay.com")
        self.assert_invalid_address("gVw9TWimGFXRjoDXWhWxeNQbu84ZpLkvnenkKvA5aJeDo31eM5tC@somerelay.com:1220")
        self.assert_invalid_address("grinbox:#gVwjSsYW5vvHpK4AunJ5piKhhQTV6V3Jb818Uqs6PdC3SsB36AsA@somerelay.com")
        self.assert_invalid_address("grinbox:#gVwjSsYW5vvHpK4AunJ5piKhhQTV6V3Jb818Uqs6PdC3SsB36AsA@somerelay.com:1220")

        # valid IP:port addresses but not supported in Bisq
        self.assert_invalid_address("0.0.0.0:8080")
        self.assert_invalid_address("173.194.34.134:8080")
        self.assert_invalid_address("127.0.0.1:8080")
        self.assert_invalid_address("192.168.0.1:8080")
        self.assert_invalid_address("18.101.25.153:8080")
        self.assert_invalid_address("173.194.34.134:1")
        self.assert_invalid_address("173.194.34.134:11")
        self.assert_invalid_address("173.194.34.134:1111")
        self.assert_invalid_address("173.194.34.134:65535")

        # invalid IP:port addresses
        self.assert_invalid_address("google.com")
        self.assert_invalid_address("100.100.100.100")
        self.assert_invalid_address(".100.100.100.100:1222")
        self.assert_invalid_address("100..100.100.100:1222.")
        self.assert_invalid_address("100.100.100.100.:1222")
        self.assert_invalid_address("999.999.999.999:1222")
        self.assert_invalid_address("256.256.256.256:1222")
        self.assert_invalid_address("256.100.100.100.100:1222")
        self.assert_invalid_address("123.123.123:1222")
        self.assert_invalid_address("http:#123.123.123:1222")
        self.assert_invalid_address("1000.2.3.4:1222")
        self.assert_invalid_address("999.2.3.4:1222")
        # too large port
        self.assert_invalid_address("173.194.34.134:65536")

        self.assert_invalid_address("gVvk7rLBg3r3qoWYL3VsREnBbooT7nynxx5HtDvUWCJUaNCnddvY1111")
        self.assert_invalid_address("grinbox:/gVtWzX5NTLCBkyNV19QVdnLXue13heAVRD36sfkGD6xpqy7k7e4a")
        self.assert_invalid_address("gVw9TWimGFXRjoDXWhWxeNQbu84ZpLkvnenkKvA5aJeDo31eM5tC@somerelay.com.")
        self.assert_invalid_address("gVw9TWimGFXRjoDXWhWxeNQbu84ZpLkvnenkKvA5aJeDo31eM5tC@somerelay.com:1220a")
        self.assert_invalid_address("grinbox:#gVwjSsYW5vvHpK4AunJ5piKhhQTV6V3Jb818Uqs6PdC3SsB36AsAsomerelay.com")
        self.assert_invalid_address("grinbox:#gVwjSsYW5vvHpK4AunJ5piKhhQTV6V3Jb818Uqs6PdC3SsB36AsA@somerelay.com1220")


if __name__ == '__main__':
    unittest.main()