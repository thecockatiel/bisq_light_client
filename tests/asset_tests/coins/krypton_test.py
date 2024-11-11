import unittest
from bisq.asset.coins.krypton import Krypton
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class KryptonTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Krypton())
    
    def test_valid_addresses(self):
        self.assert_valid_address("QQQ1LgQ1m8vX5tGrBZ2miS7A54Fmj5Qbij4UXT8nD4aqF75b1cpAauxVkjYaefcztV62UrDT1K9WHDeQWu4vpVXU2wezpshvex")
        self.assert_valid_address("QQQ1G56SKneSK1833tKjLH7E4ZgFwnqhqUb1HMHgYbnhaST56mukM1296jiYjTyTdMWnvH5FpWNAJWaQqwyPJHUR8qXRKBJy9o")
        self.assert_valid_address("QQQ1Bg61uUZhsNaTmUSZNcFgX2bk9wnAoYg9DSYZidDMJt7wVyccvMy8J7zRBoV5iT1pbraFUDWPQWWdXGPPws2P2ZGe8UzsaJ")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("QQQ1Bg61uUZhsNaTmUSZNcFgX2bk9wnAoYg9DSYZidDMJt7wVyccvMy8J7zRBoV5iT1pbraFUDWPQWWdXGPPws2P2ZGe8")
        self.assert_invalid_address("11QQQ1Bg61uUZhsNaTmUSZNcFgX2bk9wnAoYg9DSYZidDMJt7wVyccvMy8J7zRBoV5iT1pbraFUDWPQWWdXGPPws2P2ZGe8UzsaJ")
        self.assert_invalid_address("")
        self.assert_invalid_address("#RoUKWRwpsx1F")
        self.assert_invalid_address("YQQ1G56SKneSK1833tKjLH7E4ZgFwnqhqUb1HMHgYbnhaST56mukM1296jiYjTyTdMWnvH5FpWNAJWaQqwyPJHUR8qXRKBJy9o")
        self.assert_invalid_address("3jyRo3rcp9fjdfjdSGpx")
        self.assert_invalid_address("QQQ1G56SKneSK1833tKjLH7E4ZgFwnqhqUb1HMHgYbnhaST56mukM1296jiYjTyTdMWnvH5FpWNAJWaQqwyPJHUR8qXRKBJy9#")
        self.assert_invalid_address("ZOD1Bg61uUZhsNaTmUSZNcFgX2bk9wnAoYg9DSYZidDMJt7wVyccvMy8J7zRBoV5iT1pbraFUDWPQWWdXGPPws2P2ZGe8UzsaJ")


if __name__ == '__main__':
    unittest.main()