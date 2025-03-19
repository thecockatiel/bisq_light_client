import unittest

from bisq.core.xmr.knaccc.monero.address.wallet_address import WalletAddress


class WalletAddressTest(unittest.TestCase):

    def test_wallet_address(self):
        main_address = "43amHgM9cDHhJY8tAujYi4MisCx4dvNQB5xVYbRLqPYLbVmH5qHcUgsjgsdoSdLK3TgRaBd68bCLaRcK8VakCUAJLGjz42G"
        wallet_address = WalletAddress(main_address)

        private_view_key_hex = (
            "7b37d8922245a07244fd31855d1e705a590a9bd2881825f0542ad99cdaba090a"
        )
        public_view_key_hex = (
            "3cd5a3079e8b4cff3630ce16bfda6eebb2da86169accdb93206a92a58d586faa"
        )

        subaddress_01 = wallet_address.get_subaddress_base58(private_view_key_hex, 0, 1)
        subaddress_10 = wallet_address.get_subaddress_base58(private_view_key_hex, 1, 0)
        subaddress_11 = wallet_address.get_subaddress_base58(private_view_key_hex, 1, 1)

        self.assertEqual(wallet_address.base58, main_address)
        self.assertEqual(
            subaddress_01,
            "8B3QYUXKj8ySWiCaF79NyS6RJBkkRmNpQiCMKHkHhE7J67joNdt1Wf7gxFKw8EnXxofpVhdSsg61JQnR2jbeEyW2CM5sqvY",
        )
        self.assertEqual(
            subaddress_10,
            "83YULqcGNVzMA4ehBN8uwP4tiJYGBw3Zo8LAEod1rtvd4WfATg9LHZbd8tbnNrosb3Fri7HdXSPyF2hPBQend6A3LQWymPt",
        )
        self.assertEqual(
            subaddress_11,
            "8AZFX2Ledf8hhb5RTt9vsbGfc6CJW4SviWMgpFy9LCmKJzg6ZCyKR2nEBtiz8v8QXheoCPLFGi1HpEtyBju8aUA6Bkreqhr",
        )

        self.assertTrue(wallet_address.check_private_view_key(private_view_key_hex))
        self.assertTrue(
            WalletAddress.does_private_key_resolve_to_public_key(
                private_view_key_hex, public_view_key_hex
            )
        )
        self.assertFalse(
            WalletAddress.does_private_key_resolve_to_public_key(
                private_view_key_hex, private_view_key_hex
            )
        )

        self.assertTrue(
            WalletAddress.does_private_key_resolve_to_public_key(
                "a82a9017a1d259c71f5392ad9091b743b86dac7a21f5e402ea0a55e5c8a6750f",
                "bdc158199c8933353627d54edb4bbae547dbbde3130860d7940313210edca0a6",
            )
        )

        self.assertTrue(
            WalletAddress.does_private_key_resolve_to_public_key(
                "dae1bceeb2563b8c376f8e0456e5fe7aa3d6291b38ace18c6ad5647424a3b104",
                "d17698d07fe9edbc41552299b90a93de73bb1bd4b94b8083af0bbe3a1931e2ec",
            )
        )

        self.assertFalse(
            WalletAddress.does_private_key_resolve_to_public_key(
                "0000111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF",
                "0000111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF",
            )
        )

        non_reduced_private_key = (
            "680bceef3ca8b2ca1a9a29283c184f6f590a9bd2881825f0542ad99cdaba091a"
        )
        self.assertFalse(WalletAddress.is_private_key_reduced(non_reduced_private_key))
        self.assertTrue(WalletAddress.is_private_key_reduced(private_view_key_hex))


if __name__ == "__main__":
    unittest.main()
