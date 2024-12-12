import unittest

from bisq.core.util.regex_validator_factory import RegexValidatorFactory

class RegexValidatorTest(unittest.TestCase):
    def test_address_regex_validator(self):
        regex_validator = RegexValidatorFactory.address_regex_validator()

        # Empty string tests
        self.assertTrue(regex_validator.validate("").is_valid)
        self.assertFalse(regex_validator.validate(" ").is_valid)

        # Onion V2 addresses
        self.assertTrue(regex_validator.validate("abcdefghij234567.onion").is_valid)
        self.assertTrue(regex_validator.validate("abcdefghijklmnop.onion,abcdefghijklmnop.onion").is_valid)
        self.assertTrue(regex_validator.validate("abcdefghijklmnop.onion, abcdefghijklmnop.onion").is_valid)
        self.assertTrue(regex_validator.validate("qrstuvwxyzABCDEF.onion,qrstuvwxyzABCDEF.onion,aaaaaaaaaaaaaaaa.onion").is_valid)
        self.assertTrue(regex_validator.validate("GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertTrue(regex_validator.validate("WXYZ234567abcdef.onion,GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertTrue(regex_validator.validate("aaaaaaaaaaaaaaaa.onion:9999,WXYZ234567abcdef.onion:9999,2222222222222222.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcd.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop,abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghi2345689.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("onion:9999,abcdefghijklmnop.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion:").is_valid)

        # Onion V3 addresses
        self.assertFalse(regex_validator.validate("32zzibxmqi2ybxpqyggwwuwz7a3lbvtzoloti7cxoevyvijexvgsfei.onion:8333").is_valid) # 1 missing char
        self.assertTrue(regex_validator.validate("wizseed7ab2gi3x267xahrp2pkndyrovczezzb46jk6quvguciuyqrid.onion:8000").is_valid)

        # IPv4 addresses
        self.assertTrue(regex_validator.validate("12.34.56.78").is_valid)
        self.assertTrue(regex_validator.validate("12.34.56.78,87.65.43.21").is_valid)
        self.assertTrue(regex_validator.validate("12.34.56.78:8888").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.788").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78:").is_valid)

        # IPv6 addresses
        self.assertTrue(regex_validator.validate("FE80:0000:0000:0000:0202:B3FF:FE1E:8329").is_valid)
        self.assertTrue(regex_validator.validate("FE80::0202:B3FF:FE1E:8329").is_valid)
        self.assertTrue(regex_validator.validate("FE80::0202:B3FF:FE1E:8329,FE80:0000:0000:0000:0202:B3FF:FE1E:8329").is_valid)
        self.assertTrue(regex_validator.validate("::1").is_valid)
        self.assertTrue(regex_validator.validate("fe80::").is_valid)
        self.assertTrue(regex_validator.validate("2001::").is_valid)
        self.assertTrue(regex_validator.validate("[::1]:8333").is_valid)
        self.assertTrue(regex_validator.validate("[FE80::0202:B3FF:FE1E:8329]:8333").is_valid)
        self.assertTrue(regex_validator.validate("[2001:db8::1]:80").is_valid)
        self.assertTrue(regex_validator.validate("[aaaa::bbbb]:8333").is_valid)
        self.assertFalse(regex_validator.validate("1200:0000:AB00:1234:O000:2552:7777:1313").is_valid)

        # FQDN addresses
        self.assertTrue(regex_validator.validate("example.com").is_valid)
        self.assertTrue(regex_validator.validate("mynode.local:8333").is_valid)
        self.assertTrue(regex_validator.validate("foo.example.com,bar.example.com").is_valid)
        self.assertTrue(regex_validator.validate("foo.example.com:8333,bar.example.com:8333").is_valid)
        self.assertFalse(regex_validator.validate("mynode.local:65536").is_valid)
        self.assertFalse(regex_validator.validate("-example.com").is_valid)
        self.assertFalse(regex_validator.validate("example-.com").is_valid)

    def test_onion_address_regex_validator(self):
        regex_validator = RegexValidatorFactory.onion_address_regex_validator()

        self.assertTrue(regex_validator.validate("").is_valid)
        self.assertFalse(regex_validator.validate(" ").is_valid)

        # Onion V2 addresses
        self.assertTrue(regex_validator.validate("abcdefghij234567.onion").is_valid)
        self.assertTrue(regex_validator.validate("abcdefghijklmnop.onion,abcdefghijklmnop.onion").is_valid)
        self.assertTrue(regex_validator.validate("abcdefghijklmnop.onion, abcdefghijklmnop.onion").is_valid)
        self.assertTrue(regex_validator.validate("qrstuvwxyzABCDEF.onion,qrstuvwxyzABCDEF.onion,aaaaaaaaaaaaaaaa.onion").is_valid)
        self.assertTrue(regex_validator.validate("GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertTrue(regex_validator.validate("WXYZ234567abcdef.onion,GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertTrue(regex_validator.validate("aaaaaaaaaaaaaaaa.onion:9999,WXYZ234567abcdef.onion:9999,2222222222222222.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcd.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop,abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghi2345689.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("onion:9999,abcdefghijklmnop.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion:").is_valid)

        # Onion V3 addresses
        self.assertFalse(regex_validator.validate("32zzibxmqi2ybxpqyggwwuwz7a3lbvtzoloti7cxoevyvijexvgsfei.onion:8333").is_valid)  # 1 missing char
        self.assertTrue(regex_validator.validate("wizseed7ab2gi3x267xahrp2pkndyrovczezzb46jk6quvguciuyqrid.onion:8000").is_valid)

    def test_localhost_address_regex_validator(self):
        regex_validator = RegexValidatorFactory.localhost_address_regex_validator()

        self.assertTrue(regex_validator.validate("").is_valid)
        self.assertFalse(regex_validator.validate(" ").is_valid)

        # Onion V2 addresses
        self.assertFalse(regex_validator.validate("abcdefghij234567.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion,abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion, abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("qrstuvwxyzABCDEF.onion,qrstuvwxyzABCDEF.onion,aaaaaaaaaaaaaaaa.onion").is_valid)
        self.assertFalse(regex_validator.validate("GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("WXYZ234567abcdef.onion,GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("aaaaaaaaaaaaaaaa.onion:9999,WXYZ234567abcdef.onion:9999,2222222222222222.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcd.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop,abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghi2345689.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("onion:9999,abcdefghijklmnop.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion:").is_valid)

        # Onion V3 addresses
        self.assertFalse(regex_validator.validate("32zzibxmqi2ybxpqyggwwuwz7a3lbvtzoloti7cxoevyvijexvgsfei.onion:8333").is_valid)  # 1 missing char
        self.assertFalse(regex_validator.validate("wizseed7ab2gi3x267xahrp2pkndyrovczezzb46jk6quvguciuyqrid.onion:8000").is_valid)

        # IPv4 addresses
        self.assertFalse(regex_validator.validate("12.34.56.78").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78,87.65.43.21").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78:8888").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.788").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78:").is_valid)

        # IPv4 loopback addresses
        self.assertTrue(regex_validator.validate("127.0.0.1").is_valid)
        self.assertTrue(regex_validator.validate("127.0.1.1").is_valid)

        # IPv4 local addresses
        self.assertFalse(regex_validator.validate("10.10.10.10").is_valid)
        self.assertFalse(regex_validator.validate("172.19.1.1").is_valid)
        self.assertFalse(regex_validator.validate("172.19.1.1").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.1").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.1,172.16.1.1").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.1:8888,192.168.1.2:8888").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.888").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.1:").is_valid)

        # IPv4 autolocal addresses
        self.assertFalse(regex_validator.validate("169.254.123.232").is_valid)

        # IPv6 local addresses
        self.assertFalse(regex_validator.validate("fe80::").is_valid)
        self.assertFalse(regex_validator.validate("fc00::").is_valid)
        self.assertFalse(regex_validator.validate("fd00::8").is_valid)
        self.assertFalse(regex_validator.validate("fd00::7:8").is_valid)
        self.assertFalse(regex_validator.validate("fd00::6:7:8").is_valid)
        self.assertFalse(regex_validator.validate("fd00::5:6:7:8").is_valid)
        self.assertFalse(regex_validator.validate("fd00::3:4:5:6:7:8").is_valid)
        self.assertFalse(regex_validator.validate("fd00::4:5:6:7:8").is_valid)
        self.assertFalse(regex_validator.validate("fd00:2:3:4:5:6:7:8").is_valid)
        self.assertFalse(regex_validator.validate("fd00::0202:B3FF:FE1E:8329").is_valid)

        self.assertFalse(regex_validator.validate("FE80:0000:0000:0000:0202:B3FF:FE1E:8329").is_valid)
        self.assertFalse(regex_validator.validate("FE80::0202:B3FF:FE1E:8329").is_valid)
        self.assertFalse(regex_validator.validate("FE80::0202:B3FF:FE1E:8329,FE80:0000:0000:0000:0202:B3FF:FE1E:8329").is_valid)
        # IPv6 local with optional port at the end
        self.assertFalse(regex_validator.validate("[fd00::1]:8081").is_valid)
        self.assertFalse(regex_validator.validate("[fd00::1]:8081,[fc00::1]:8081").is_valid)

        # IPv6 loopback
        self.assertTrue(regex_validator.validate("::1").is_valid)
        self.assertTrue(regex_validator.validate("::2").is_valid)
        self.assertTrue(regex_validator.validate("[::1]:8333").is_valid)

        # IPv6 unicast
        self.assertFalse(regex_validator.validate("2001::").is_valid)
        self.assertFalse(regex_validator.validate("[FE80::0202:B3FF:FE1E:8329]:8333").is_valid)
        self.assertFalse(regex_validator.validate("[2001:db8::1]:80").is_valid)
        self.assertFalse(regex_validator.validate("[aaaa::bbbb]:8333").is_valid)
        self.assertFalse(regex_validator.validate("1200:0000:AB00:1234:O000:2552:7777:1313").is_valid)

        # Localhost FQDN hostnames
        self.assertTrue(regex_validator.validate("localhost").is_valid)
        self.assertTrue(regex_validator.validate("localhost:8081").is_valid)

        # Local FQDN hostnames
        self.assertFalse(regex_validator.validate("mynode.local:8081").is_valid)

        # Non-local FQDN hostnames
        self.assertFalse(regex_validator.validate("example.com").is_valid)
        self.assertFalse(regex_validator.validate("foo.example.com,bar.example.com").is_valid)
        self.assertFalse(regex_validator.validate("foo.example.com:8333,bar.example.com:8333").is_valid)

        # Invalid FQDN hostnames
        self.assertFalse(regex_validator.validate("mynode.local:65536").is_valid)
        self.assertFalse(regex_validator.validate("-example.com").is_valid)
        self.assertFalse(regex_validator.validate("example-.com").is_valid)
        
        
    def test_localnet_address_regex_validator(self):
        regex_validator = RegexValidatorFactory.localnet_address_regex_validator()

        self.assertTrue(regex_validator.validate("").is_valid)
        self.assertFalse(regex_validator.validate(" ").is_valid)

        # Onion V2 addresses
        self.assertFalse(regex_validator.validate("abcdefghij234567.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion,abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion, abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("qrstuvwxyzABCDEF.onion,qrstuvwxyzABCDEF.onion,aaaaaaaaaaaaaaaa.onion").is_valid)
        self.assertFalse(regex_validator.validate("GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("WXYZ234567abcdef.onion,GHIJKLMNOPQRSTUV.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("aaaaaaaaaaaaaaaa.onion:9999,WXYZ234567abcdef.onion:9999,2222222222222222.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcd.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop,abcdefghijklmnop.onion").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghi2345689.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("onion:9999,abcdefghijklmnop.onion:9999").is_valid)
        self.assertFalse(regex_validator.validate("abcdefghijklmnop.onion:").is_valid)

        # Onion V3 addresses
        self.assertFalse(regex_validator.validate("32zzibxmqi2ybxpqyggwwuwz7a3lbvtzoloti7cxoevyvijexvgsfei.onion:8333").is_valid)  # 1 missing char
        self.assertFalse(regex_validator.validate("wizseed7ab2gi3x267xahrp2pkndyrovczezzb46jk6quvguciuyqrid.onion:8000").is_valid)

        # IPv4 addresses
        self.assertFalse(regex_validator.validate("12.34.56.78").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78,87.65.43.21").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78:8888").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.788").is_valid)
        self.assertFalse(regex_validator.validate("12.34.56.78:").is_valid)

        # IPv4 local addresses
        self.assertTrue(regex_validator.validate("10.10.10.10").is_valid)
        self.assertTrue(regex_validator.validate("172.19.1.1").is_valid)
        self.assertTrue(regex_validator.validate("172.19.1.1").is_valid)
        self.assertTrue(regex_validator.validate("192.168.1.1").is_valid)
        self.assertTrue(regex_validator.validate("192.168.1.1,172.16.1.1").is_valid)
        self.assertTrue(regex_validator.validate("192.168.1.1:8888,192.168.1.2:8888").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.888").is_valid)
        self.assertFalse(regex_validator.validate("192.168.1.1:").is_valid)

        # IPv4 autolocal addresses
        self.assertTrue(regex_validator.validate("169.254.123.232").is_valid)

        # IPv6 local addresses
        self.assertTrue(regex_validator.validate("fe80:2:3:4:5:6:7:8").is_valid)
        self.assertTrue(regex_validator.validate("fe80::").is_valid)
        self.assertTrue(regex_validator.validate("fc00::").is_valid)
        self.assertTrue(regex_validator.validate("fd00::,fe80::1").is_valid)
        self.assertTrue(regex_validator.validate("fd00::8").is_valid)
        self.assertTrue(regex_validator.validate("fd00::7:8").is_valid)
        self.assertTrue(regex_validator.validate("fd00::6:7:8").is_valid)
        self.assertTrue(regex_validator.validate("fd00::5:6:7:8").is_valid)
        self.assertTrue(regex_validator.validate("fd00::4:5:6:7:8").is_valid)
        self.assertTrue(regex_validator.validate("fd00::3:4:5:6:7:8").is_valid)
        self.assertTrue(regex_validator.validate("fd00:2:3:4:5:6:7:8").is_valid)
        self.assertTrue(regex_validator.validate("fd00::0202:B3FF:FE1E:8329").is_valid)
        self.assertTrue(regex_validator.validate("fd00::0202:B3FF:FE1E:8329,FE80::0202:B3FF:FE1E:8329").is_valid)
        # IPv6 local with optional port at the end
        self.assertTrue(regex_validator.validate("[fd00::1]:8081").is_valid)
        self.assertTrue(regex_validator.validate("[fd00::1]:8081,[fc00::1]:8081").is_valid)
        self.assertTrue(regex_validator.validate("[FE80::0202:B3FF:FE1E:8329]:8333").is_valid)

        # IPv6 loopback
        self.assertFalse(regex_validator.validate("::1").is_valid)

        # IPv6 unicast
        self.assertFalse(regex_validator.validate("2001::").is_valid)
        self.assertFalse(regex_validator.validate("[::1]:8333").is_valid)
        self.assertFalse(regex_validator.validate("[2001:db8::1]:80").is_valid)
        self.assertFalse(regex_validator.validate("[aaaa::bbbb]:8333").is_valid)
        self.assertFalse(regex_validator.validate("1200:0000:AB00:1234:O000:2552:7777:1313").is_valid)

        # *.local FQDN hostnames
        self.assertTrue(regex_validator.validate("mynode.local").is_valid)
        self.assertTrue(regex_validator.validate("mynode.local:8081").is_valid)

        # Non-local FQDN hostnames
        self.assertFalse(regex_validator.validate("example.com").is_valid)
        self.assertFalse(regex_validator.validate("foo.example.com,bar.example.com").is_valid)
        self.assertFalse(regex_validator.validate("foo.example.com:8333,bar.example.com:8333").is_valid)

        # Invalid FQDN hostnames
        self.assertFalse(regex_validator.validate("mynode.local:65536").is_valid)
        self.assertFalse(regex_validator.validate("-example.com").is_valid)
        self.assertFalse(regex_validator.validate("example-.com").is_valid)

if __name__ == '__main__':
    unittest.main()


