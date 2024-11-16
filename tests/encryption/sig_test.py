import base64
import unittest

from bisq.common.crypto.sig import Sig

class TestEncryption(unittest.TestCase):
    def setUp(self):
        # These hex examples come from running the java codes from Encryption class on bisq/core/common/crypto/encryption.java
        self.public_hex = "308201b73082012c06072a8648ce3804013082011f02818100fd7f53811d75122952df4a9c2eece4e7f611b7523cef4400c31e3f80b6512669455d402251fb593d8d58fabfc5f5ba30f6cb9b556cd7813b801d346ff26660b76b9950a5a49f9fe8047b1022c24fbba9d7feb7c61bf83b57e7c6a8a6150f04fb83f6d3c51ec3023554135a169132f675f3ae2b61d72aeff22203199dd14801c70215009760508f15230bccb292b982a2eb840bf0581cf502818100f7e1a085d69b3ddecbbcab5c36b857b97994afbbfa3aea82f9574c0b3d0782675159578ebad4594fe67107108180b449167123e84c281613b7cf09328cc8a6e13c167a8b547c8d28e0a3ae1e2bb3a675916ea37f0bfa213562f1fb627a01243bcca4f1bea8519089a883dfe15ae59f06928b665e807b552564014c3bfecf492a03818400028180271aa0e3a61563971ba3e76ade5f7c3275f71ba662f6a6cddd53016d983989179b75dd13c5cb8a7ac8950dc2496470e3b43848f2a5b8dd7989097c71296bf0934af7a7a2f1d4428db5bd14a8e27c59792a965a1b0c430d1f06243e78e60b227f856215dcfa3c273c605a7afd53cc20f02ec861b5397639be12a43f0b3a7cb2ff"
        self.private_hex = "3082014b0201003082012c06072a8648ce3804013082011f02818100fd7f53811d75122952df4a9c2eece4e7f611b7523cef4400c31e3f80b6512669455d402251fb593d8d58fabfc5f5ba30f6cb9b556cd7813b801d346ff26660b76b9950a5a49f9fe8047b1022c24fbba9d7feb7c61bf83b57e7c6a8a6150f04fb83f6d3c51ec3023554135a169132f675f3ae2b61d72aeff22203199dd14801c70215009760508f15230bccb292b982a2eb840bf0581cf502818100f7e1a085d69b3ddecbbcab5c36b857b97994afbbfa3aea82f9574c0b3d0782675159578ebad4594fe67107108180b449167123e84c281613b7cf09328cc8a6e13c167a8b547c8d28e0a3ae1e2bb3a675916ea37f0bfa213562f1fb627a01243bcca4f1bea8519089a883dfe15ae59f06928b665e807b552564014c3bfecf492a041602143aa9d8a87d70434f07a85d3bb367363f91758fc6"
        self.text_message = "TestIsGood"
        self.text_message_signature_hex = "302c02142fd9d8d8894453ff3d279798e1f9340e5e05331c021451734d432c7c2b1bef21f5c52dbedec97c4c67e7"

    def test_encrypt_decrypt_payload(self):
        privkey = Sig.get_private_key_from_bytes(bytes.fromhex(self.private_hex))
        pubkey = Sig.get_public_key_from_bytes(bytes.fromhex(self.public_hex))
        signature = Sig.sign(privkey, self.text_message.encode())
        self.assertTrue(Sig.verify(pubkey, self.text_message.encode(), signature))
    
    def test_encrypt_decrypt_payload_with_provided_key(self):
        privkey = Sig.get_private_key_from_bytes(bytes.fromhex(self.private_hex))
        pubkey = Sig.get_public_key_from_bytes(bytes.fromhex(self.public_hex))
        signature = Sig.sign_message(privkey, self.text_message)
        self.assertTrue(Sig.verify_message(pubkey, self.text_message, signature))
        self.assertTrue(Sig.verify_message(pubkey, self.text_message, base64.b64encode(bytes.fromhex(self.text_message_signature_hex)).decode('utf-8')))

if __name__ == '__main__':
    unittest.main()