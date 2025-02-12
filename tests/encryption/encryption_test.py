import base64
import unittest

from bisq.common.crypto.encryption import Encryption, ECPrivkey, rsa
from bisq.common.crypto.sig import Sig
from bisq.core.alert.alert import Alert

class TestEncryption(unittest.TestCase):
    def setUp(self):
        # These hex examples come from running the java codes from Encryption class on bisq/core/common/crypto/encryption.java
        self.public_hex = "30820122300d06092a864886f70d01010105000382010f003082010a0282010100ecafdf33938e1f3c369439fc3115fdd55cb52ab070b3b80f992e5938defce4d6d12f34025f748675453576eb9e73d8ddb9c451820400458132278d35a72ade5d21ad1ebe6ea0bb28bd8fd929e5d32aafdb53411b77013665dd3c5adaef5705ceba23ee84a3376bbe09a463c0cf7a2a7a4cbbac1cb89bd6d0a89cf3f2f7ca56fbb625058bbe8c7f9324b825609d50afd290e791721caa74131178bc194d82082eea53ad581a9019d586728ac56cd92449a4ea88dbdd2067232a97f6e0105a7bf4543fbf1fbba41dfac10d93a6b8e93b3120834e19f14944e0d630c192cdae5101e2cddab73fcb6b4fd6038b3526166c880bdbdd6787c01ac5ac93d3d5c0cbc77f0203010001"
        self.private_hex = "308204be020100300d06092a864886f70d0101010500048204a8308204a40201000282010100ecafdf33938e1f3c369439fc3115fdd55cb52ab070b3b80f992e5938defce4d6d12f34025f748675453576eb9e73d8ddb9c451820400458132278d35a72ade5d21ad1ebe6ea0bb28bd8fd929e5d32aafdb53411b77013665dd3c5adaef5705ceba23ee84a3376bbe09a463c0cf7a2a7a4cbbac1cb89bd6d0a89cf3f2f7ca56fbb625058bbe8c7f9324b825609d50afd290e791721caa74131178bc194d82082eea53ad581a9019d586728ac56cd92449a4ea88dbdd2067232a97f6e0105a7bf4543fbf1fbba41dfac10d93a6b8e93b3120834e19f14944e0d630c192cdae5101e2cddab73fcb6b4fd6038b3526166c880bdbdd6787c01ac5ac93d3d5c0cbc77f0203010001028201001d795c93b3d27521a3f05074e4789c7151f2a8e6c0ef786d24d7b33a544bc22edd6cd7395bc160846bad17ea892db1a4bc3498d6812b617c65b9017f86c4dd5cfea116dcd85cec01a0f2dab464cf7cecda4f4df7c96edd632654ea41824ae01e6ebff9120bb08e9a6336aa9f6b96dc81a4b03d8e1eba755a959764aa43362f74e55a4c31cadf7ce77a88637fd6f7081c18487d39068bfaa7e0e6d0a695cf2e0b56cef9b3ccf1beb56a874d3b4365cde351bdc151d710bcf499b2f4a3efa79d986adc320a468746cf78627b656bf7348fbe2e2d3779f887c0a02aa54cae60600e1dbaa273d1fa843f419837e766eb5d0161bf90ccd53e5d6f29c38477deda9b9902818100f459956d06660673017f74d0bb404dc15362a0ef13d0cffbd9dd8b6a2aab3f69e5f34cd5fe2ca96eafe9d45db61240c13aec74cc95386ae83591bf241a0fe996fc445855b5bfc5d729d798a445aba4998a672e875f0b475788935ca45003c1460522513a0f4bf25b6b2342d40c6b0ce75da1c6bdc48bc284a00a81cfbc9cb12902818100f7f8c213a24323dceaf4def56d8674920e7ef55e4343383310a56f786e72d9a676c8185bb78deac620738693c6ddda0a476c2c51e502bc8183c5fb1fc2c1d5f2326e50fa92ca5b0dc1f234cae57bfbd4369765d7b8b45471204ce4f894a5962774656dd18e573302d75fb1d3123b6b05b2dda533eaa36c8706609b9b254c80670281801467dacbb50a1625ca8d3b532720129e3f797019271d7c10fb3bbe25ca946c824a7acc02deec19e62d78a88c7ee4fd5565b75375b64c74d91988275f3b71f2bef2283efc4166577e457744bf0b366f53873460b55b6194bea1a034cf60034043b9b008fa81468561cf0badcc0991730d6b4b544e8ab8653130305070e9be682902818100988a1b012ef0f44fc2ed4d7656a0be76d699fce0b6a9d4197da4f73473650d449c8f2c84c71e730cdc0b94feb4f7e6582a657dc20709aee2512869f9b8b9ba9d99ae48fc4b6e55a2d9eadfd4ec645f9ec4d24f60eb8b6ae2884725175181a723b03370e1d7190715395df1aaf0ed4241a82d36a20035f5ddfdeb51ed977d3f0302818100bb16376b8ee5a8dd5b232b7a45450e46d1beca49c71d9811ec8ec4e349090fe6b5f2f39de5fc8c8bc2311bdfa28904e0b3eb7c7033ba8a95a76705203c8623fe94e535619b08b39ed1878916222c8985ceb97e34986f8af29f7ebc7d2e6124cdcdd64c141a687475f40595d7b0282e52fe12468e03b7020e63eb837d13c0e849"
        self.secret_key_hex = "515d0c77a4eabf2966c3f22630717a08779a065c2f1f130a5d2d5ae273f8434f"
        self.text_message = "TestIsGood"
        self.text_message_encrypted_hex = "0e45c06452aef79daef11e59c39edf99" 
        self.text_message_encrypted_hex_with_hmac = "2e1101016bbaaba5bcf65b117ae9c8fd67b0fe766fc0046db35eae537b3e783ce3d1a546d4cad4ed3964bb9fb98f9dc8"
        self.encrypted_secret_key_using_pub_key_hex = "5113c6b42bb6e31e7f39e8718e8d55023048054f01b4d1e8a5c57ad6a4180b7ab5c890c6ce96046d3bc238c826e610da78a7fea7ac5ba26846006ada6c60618971ad10e36d76ef5b8d3e2a49bb7f036f405d457365e266d4c003fa34ecb4a53bf07234b99055bc1d6a0c2ecf7b05ac2fbbeb83d2e4d37db0cdb42097e5930938cdb12efc65fce67562251d761a3a1e4a6278dfb931d30add8c0b8ff8d83857e9fc9a2eedf4de0512f9580220a529af486b29c6b634b7d936c876bf9f1dd35f97135d9238af13f2add2f383a13d138bb3f275b7e43609344f428e48c5d6a33e45042cbde8b558b7d439b3120ef5371c2e4273859234daf93ba82025380a87687a"
        self.text_message_hmac_encoded_with_secret_key_as_hex = "cfc632c94587cc6cce2c418c001ca469e79c284dfedeb0d7f44d265ad31c60e8"
        self.text_message_payload_with_hmac_hex = "546573744973476f6f64cfc632c94587cc6cce2c418c001ca469e79c284dfedeb0d7f44d265ad31c60e8"

    def test_generated_secret_hex_length(self):
        secret_key = Encryption.generate_secret_key(256).hex()
        self.assertEqual(len(secret_key), len(self.secret_key_hex))

    def test_encrypt_decrypt_payload(self):
        secret_key = bytes.fromhex(self.secret_key_hex)
        encrypted_payload = Encryption.encrypt(self.text_message.encode(), secret_key)
        decrypted_payload = Encryption.decrypt(encrypted_payload, secret_key)
        self.assertEqual(encrypted_payload.hex(), self.text_message_encrypted_hex)
        self.assertEqual(decrypted_payload.decode(), self.text_message)

    def test_encrypt_decrypt_payload_with_hmac(self):
        secret_key = bytes.fromhex(self.secret_key_hex)
        encrypted_payload_with_hmac = Encryption.encrypt_payload_with_hmac(self.text_message.encode(), secret_key)
        decrypted_payload = Encryption.decrypt_payload_with_hmac(encrypted_payload_with_hmac, secret_key)
        self.assertEqual(encrypted_payload_with_hmac.hex(), self.text_message_encrypted_hex_with_hmac)
        self.assertEqual(decrypted_payload.decode(), self.text_message)

    def test_encrypt_decrypt_secret_key(self):
        public_key = Encryption.get_public_key_from_bytes(bytes.fromhex(self.public_hex))
        private_key = Encryption.get_private_key_from_bytes(bytes.fromhex(self.private_hex))
        encrypted_secret_key = Encryption.encrypt_secret_key(bytes.fromhex(self.secret_key_hex), public_key)
        decrypted_secret_key = Encryption.decrypt_secret_key(encrypted_secret_key, private_key)
        self.assertEqual(len(encrypted_secret_key.hex()), len(self.encrypted_secret_key_using_pub_key_hex))
        self.assertEqual(decrypted_secret_key.hex(), self.secret_key_hex)

    def test_aes_encrypt_decrypt_from_java_encoded_secret_key(self):
        key = bytes.fromhex("56189c952bdde1cc5c65d4e713b855ef")
        decrypted_msg = Encryption.decrypt(bytes.fromhex("bee28106ebbcc0a4a59d8056b29f6af4"), key)
        self.assertEqual(decrypted_msg, bytes([1,2,3])) 
    
    def test_hmac(self):
        secret_key = bytes.fromhex(self.secret_key_hex)
        payload = self.text_message.encode()
        hmac = Encryption.get_hmac(payload, secret_key)
        self.assertTrue(Encryption.verify_hmac(payload, hmac, secret_key))
        self.assertTrue(Encryption.verify_hmac(payload, bytes.fromhex(self.text_message_hmac_encoded_with_secret_key_as_hex), secret_key))
        self.assertFalse(Encryption.verify_hmac(payload, bytes.fromhex("00"), secret_key))
        self.assertTrue(Encryption.get_payload_with_hmac(payload, secret_key).hex(), self.text_message_payload_with_hmac_hex)

    def test_verify_ec_message_is_from_pubkey_data_from_java(self):
        signing_key = ECPrivkey.from_secret_scalar(10)
        alert_msg_as_hex = "foo bar".encode().hex()
        try:
            Encryption.verify_ec_message_is_from_pubkey(
                alert_msg_as_hex,
                "Hyd8jbtqZS9WsAxJI8YOpZZFNoYiihN97pupWEVJoOKXXeRvE3+4u7kn0UkKwUxuAvvvROMarma9uKAV7U7QTnY=",
                signing_key.get_public_key_bytes()
            )
            verified = True
        except Exception as e:
            verified = False
        self.assertTrue(verified)
        
    def test_verify_ec_message_is_from_pubkey_flow(self):
        alert = Alert("foo bar", False, False, "1")
        alert_msg_as_hex = alert.message.encode().hex()
        signing_key = ECPrivkey.from_secret_scalar(10)
        signature_as_base64 = base64.b64encode(signing_key.sign_message(alert_msg_as_hex, True)).decode("utf-8")
        # check that it's same procedure as java as we expect
        self.assertEqual(signature_as_base64, "Hyd8jbtqZS9WsAxJI8YOpZZFNoYiihN97pupWEVJoOKXXeRvE3+4u7kn0UkKwUxuAvvvROMarma9uKAV7U7QTnY=")
        
        dsa_key = Sig.get_private_key_from_bytes(bytes.fromhex("3082014b0201003082012c06072a8648ce3804013082011f02818100fd7f53811d75122952df4a9c2eece4e7f611b7523cef4400c31e3f80b6512669455d402251fb593d8d58fabfc5f5ba30f6cb9b556cd7813b801d346ff26660b76b9950a5a49f9fe8047b1022c24fbba9d7feb7c61bf83b57e7c6a8a6150f04fb83f6d3c51ec3023554135a169132f675f3ae2b61d72aeff22203199dd14801c70215009760508f15230bccb292b982a2eb840bf0581cf502818100f7e1a085d69b3ddecbbcab5c36b857b97994afbbfa3aea82f9574c0b3d0782675159578ebad4594fe67107108180b449167123e84c281613b7cf09328cc8a6e13c167a8b547c8d28e0a3ae1e2bb3a675916ea37f0bfa213562f1fb627a01243bcca4f1bea8519089a883dfe15ae59f06928b665e807b552564014c3bfecf492a04160214494239658dfa3f12ed932725a5058510a902c85a"))
        alert.set_sig_and_pub_key(
            signature_as_base64,
            dsa_key.publickey(),
        )
        try:
            Encryption.verify_ec_message_is_from_pubkey(
                alert_msg_as_hex,
                signature_as_base64,
                signing_key.get_public_key_bytes()
            )
            verified = True
        except Exception as e:
            verified = False
        self.assertTrue(verified)

if __name__ == '__main__':
    unittest.main()