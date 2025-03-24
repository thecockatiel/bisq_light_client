import unittest
from electrum_ecc import (
    ECPrivkey,
    ECPubkey, 
    ecdsa_sig64_from_r_and_s,
    get_r_and_s_from_ecdsa_sig64,
    string_to_number,
) 


class LowRSigningKeyTest(unittest.TestCase):
    # Test vectors in format: [privKey, sigHash, expectedR, expectedS]
    GENERATED_TEST_VECTORS = [
        [
            "02",
            "546876d08f9f06f12c168f96079cd0af996ce22d89bbc58eced2631918a9bc9a",
            "45cc5d5e4fad81f2bc89f16cb37575da3ae13677f707a73ca5ca1e2787e3d311",
            "25829e0ad206dbd53cd637b75eedbde3273548673b2d08de3f61dcbe723409e2",
        ],
        [
            "02",
            "2cca2f04e6e654226483f5af39fbfebb883e301bd32553a6a0fb176b0d172b3a",
            "2bdcafead8f6db212228e52f061e894db8bdc2133c6c81a5b54883ef5648ae6d",
            "007bdcc92effb2931b4c7c5c834bf7aa847d3e0e0e1d9c7e41ed3981821eb830",
        ],
        [
            "110022003300440055006600770088009900aa00bb00cc00dd00ee00ff",
            "340b1fe486af2cd6b0ef8786d1c747fc3d785c5499d35faa25fbde57f9bf70ae",
            "2c5bc7104c059e2db8cda7b500424d2438ae2635b6cddcc51695a11e7ec95cc7",
            "62bc8969bfb02cac905f0739cecadc456bf48539a9b268b2c2725d3c2680be88",
        ],
        [
            "110022003300440055006600770088009900aa00bb00cc00dd00ee00ff",
            "44adec39be60bf10994596a0248dcafa78a45ca30472190f0de61523e90ec131",
            "1bef291f3aa99c551ef5d96d9fd06d945092e185cebe2cda75351e2f27ca3ea2",
            "2024fda909bfb9b9079f072dbe005ae850a54f16d1b59bc46afc6db2ef5461fe",
        ],
        [
            "0123456789abcdef00000000000000000123456789abcdef0000000000000000",
            "597d869fc78e5ba7eaa27b6dd418d57d90915f9e8212125002187f715510928b",
            "65f5ae18a30d1c36f4a7af7e75372e47a39e6fdde2ab33156da74bd263eae039",
            "47fa066b272a29653b9fc8111be55ef5b5de73109fd94211a0484ba9ec29fc59",
        ],
        [
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "5be2ab78309b5cf85d41d035b42b8c10d7fd69aab5d496af84c0b4760bda639f",
            "7804f6ca0c17986184affe96ae8df3c163bfa4661fbf3f9208586e30768b99a2",
            "546c91e23074e3b38b6f4cf9c72b041968f56d06f6bf2e18f03eb02423369d28",
        ],
        [
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",
            "f0f2fd0d2c8af9b1204c8320bf4453d381934afdca9ceaaa2f3fab24783b433a",
            "0cdfeff3615c787f74c01b0d40a69c75ac7f3e3aa4dd6024c570a19f0af08623",
            "04a78302a97985b7a7fcfc000d794f885c7bba0631a5f4c86c657e3993434403",
        ],
        [
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",
            "22cbd20a30c91f0ad022a185b1e3999fe1c35f64f29572ddd00781c12ea0e024",
            "74c653169f9296952fec948a92e574365b40a74596913875c6ca0ac2d864a533",
            "168bed1a949d205b9358326fcffc7ac3318fd21a1c340da727995d3c2642daff",
        ],
        # Add more test vectors as needed
    ]

    def test_sign(self):
        for (
            priv_key_hex,
            msg_hash_hex,
            expected_r_hex,
            expected_s_hex,
        ) in self.GENERATED_TEST_VECTORS:
            # Convert hex strings to bytes
            msg_hash = bytes.fromhex(msg_hash_hex)
            expected_r = string_to_number(bytes.fromhex(expected_r_hex))
            expected_s = string_to_number(bytes.fromhex(expected_s_hex))

            # Create EC private key and sign
            # priv_key = Encryption.get_ec_private_key_from_int_string_bytes(bytes.fromhex(priv_key_hex))
            # signature = Encryption.sign_with_ec_private_key(priv_key, msg_hash)

            priv_key = ECPrivkey.from_secret_scalar(
                string_to_number(bytes.fromhex(priv_key_hex))
            )
            signature = priv_key.ecdsa_sign(
                msg_hash, sigencode=ecdsa_sig64_from_r_and_s
            )

            # Extract r and s components from signature
            # r, s = decode_dss_signature(signature)
            r, s = get_r_and_s_from_ecdsa_sig64(signature)

            # Verify signature
            pub_key = ECPubkey(priv_key.get_public_key_bytes())
            self.assertTrue(pub_key.ecdsa_verify(signature, msg_hash))

            # Check if r component is low (less than 2^256)
            self.assertTrue(r.bit_length() < 256)

            # Check if signature components match expected values
            self.assertEqual(r, expected_r)
            self.assertEqual(s, expected_s)


if __name__ == "__main__":
    unittest.main()
