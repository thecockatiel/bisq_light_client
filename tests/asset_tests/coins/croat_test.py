import unittest
from bisq.asset.coins.croat import Croat
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CroatTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Croat())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("CsZ46x2mzB3GhjrC2Lt7oZ4Efmj8USUjVM7Bdz8B8EF6bQwN84NzSti7RwLZcFoZG5NR1iaiZY8GP2KwumVc1jGzHLvBzAv")
        self.assert_valid_address("CjxZDcoWCsx1wmYkmJcFpSTgqpjoFGRW9dQT8JqgwvkBaU6Q3X4MJ4QjVkNUM7GHp6NjYaTrKeH4bSRTK3mCYsHf2818vzv")
        self.assert_valid_address("CoCJje3bcEH2dkvb5suRy2ZiBtPBeBqWaY9sbMLEtqEvDn969eDx1zqV4FP8erJSJFK5Br6GheGnJJG7BDtG9XFbFcMkUJU")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("ZsZ46x2mzB3GhjrC2Lt7oZ4Efmj8USUjVM7Bdz8B8EF6bQwN84NzSti7RwLZcFoZG5NR1iaiZY8GP2KwumVc1jGzHLvBzAv")
        self.assert_invalid_address("")
        self.assert_invalid_address("CjxZDcoWCsx1wmYkmJcFpSTgqpjoFGRW9dQT8JqgwvkBaU6Q3X4MJ4QjV#NUM7GHp6NjYaTrKeH4bSRTK3mCYsHf2818vzv")
        self.assert_invalid_address("CoCJje3bcEH2dkvb5suRy2ZiBtPBeBqWaY9sbMLEtqEvDn969eDx1zqV4FP8erJSJFK5Br6GheGnJJG7BDtG9XFbFcMkUJUuuuuuuuu")
        self.assert_invalid_address("CsZ46x2mzB3GhjrC2Lt7oZ4Efmj8USUjVM7Bdz8B8EF6bQwN84NzSti7RwLZcFoZG5NR1iaiZY8GP2KwumVc1jGzHLvBzAv11111111")
        self.assert_invalid_address("CjxZDcoWCsx1wmYkmJcFpSTgqpjoFGRW9dQT8JqgwvkBaU6Q3X4MJ4QjVkNUM7GHp6NjYaTrKeH4bSRTK3m")
        self.assert_invalid_address("CjxZDcoWCsx1wmYkmJcFpSTgqpjoFGRW9dQT8JqgwvkBaU6Q3X4MJ4QjVkNUM7GHp6NjYaTrKeH4bSRTK3mCYsHf2818vzv$%")

if __name__ == '__main__':
    unittest.main()