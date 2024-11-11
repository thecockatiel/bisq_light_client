import unittest
from bisq.asset.coins.masari import Masari
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MasariTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Masari())

    def test_valid_addresses(self):  
        self.assert_valid_address("5n9Y2vwnf8oKBhHxRAyjS9aS9j5hTPjtS8RKzMbD3tP95yxkQWbUHkFhLs2UsjgNxj28W6YzNL9WFeY91xPGFXAaUwyVm1h")
        self.assert_valid_address("9n1AVze3gmj3ZpEz5Xju92FRiqtmcnQhhXJK7yx9D9qrHRvjZftndVci8HCYFttFeD7ftAMUqUGxG8iA4Sn2eVz45R2NUJj")
        self.assert_valid_address("5iB4LfuyvA5HSJP5A1xUKGb8pw5NkywxSeRZPxzy1U7kT3wBmypemQUUzTiCwjy6PTSrJpAvxiNDSUEjNryt17C8RvPdEg3")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("")
        self.assert_invalid_address("5hJpeWa9aogfpY5Su8YmeYaeuD7pyQvSZURcNx26QskbSk9UdZ6cR4HR4YsdWRiBJfCZKLHRTfj7ojGUJ7N5j5hg4pGGCE")
        self.assert_invalid_address("5kYyn6K8hRWg16nztTuvaZ6Jg3ytH84gjbUoEKjbMU4u659PKLpKuLWVSujFwJ1Qp3ZUxhcFHBXMQDmeAz46By3FRRkdaug2")
        self.assert_invalid_address("4okMfbVrFXE4nF9dRKnVLiJi2xiMDDuSk6MJexpBaNgsLutSaBN7euR8TCf4Z1dqmG85GdQHrzSpYgX8Lf2VJnkaAk9MtQV")
        self.assert_invalid_address("5jrE2mwcHkvZq9rQcvX1GCELnwAF6wwmJ4rhVdDP6y#326Gp6KSNbeWWb1sD2dmDZvczHFs8LGM1UjTQfQjjAu6S4eXGC5h")

if __name__ == "__main__":
    unittest.main()
