import unittest
from unittest.mock import Mock, patch
from bisq.common.crypto.sealed_and_signed import SealedAndSigned
import pb_pb2 as protobuf

class TestSealedAndSigned(unittest.TestCase):
    def setUp(self):
        self.mock_public_key = Mock(name='mock_dsa_public_key')
        self.test_secret_key = b'test_secret_key'
        self.test_payload = b'test_payload'
        self.test_signature = b'test_signature'
        self.test_public_key_bytes = b'test_public_key_bytes'

    @patch('bisq.common.crypto.sealed_and_signed.Sig')
    def test_init_with_public_key(self, mock_sig):
        mock_sig.get_public_key_bytes.return_value = self.test_public_key_bytes
        
        sealed = SealedAndSigned(
            encrypted_secret_key=self.test_secret_key,
            encrypted_payload_with_hmac=self.test_payload,
            signature=self.test_signature,
            sig_public_key=self.mock_public_key
        )
        
        self.assertEqual(sealed.encrypted_secret_key, self.test_secret_key)
        self.assertEqual(sealed.encrypted_payload_with_hmac, self.test_payload)
        self.assertEqual(sealed.signature, self.test_signature)
        self.assertEqual(sealed.sig_public_key, self.mock_public_key)
        self.assertEqual(sealed.sig_public_key_bytes, self.test_public_key_bytes)
        mock_sig.get_public_key_bytes.assert_called_once_with(self.mock_public_key)

    @patch('bisq.common.crypto.sealed_and_signed.Sig')
    def test_init_with_public_key_bytes(self, mock_sig):
        mock_sig.get_public_key_from_bytes.return_value = self.mock_public_key
        
        sealed = SealedAndSigned(
            encrypted_secret_key=self.test_secret_key,
            encrypted_payload_with_hmac=self.test_payload,
            signature=self.test_signature,
            sig_public_key_bytes=self.test_public_key_bytes
        )
        
        self.assertEqual(sealed.sig_public_key_bytes, self.test_public_key_bytes)
        self.assertEqual(sealed.sig_public_key, self.mock_public_key)
        mock_sig.get_public_key_from_bytes.assert_called_once_with(self.test_public_key_bytes)

    def test_init_without_keys_raises_error(self):
        with self.assertRaises(ValueError) as context:
            SealedAndSigned(
                encrypted_secret_key=self.test_secret_key,
                encrypted_payload_with_hmac=self.test_payload,
                signature=self.test_signature
            )
        self.assertEqual(str(context.exception), 
                        "Either sig_public_key or sig_public_key_bytes must be provided.")

    @patch('bisq.common.crypto.sealed_and_signed.Sig')
    def test_from_proto(self, mock_sig):
        mock_proto = Mock(spec=protobuf.SealedAndSigned)
        mock_proto.encrypted_secret_key = self.test_secret_key
        mock_proto.encrypted_payload_with_hmac = self.test_payload
        mock_proto.signature = self.test_signature
        mock_proto.sig_public_key_bytes = self.test_public_key_bytes
        
        mock_sig.get_public_key_from_bytes.return_value = self.mock_public_key
        
        sealed = SealedAndSigned.from_proto(mock_proto)
        
        self.assertEqual(sealed.encrypted_secret_key, self.test_secret_key)
        self.assertEqual(sealed.encrypted_payload_with_hmac, self.test_payload)
        self.assertEqual(sealed.signature, self.test_signature)
        self.assertEqual(sealed.sig_public_key, self.mock_public_key)
        mock_sig.get_public_key_from_bytes.assert_called_with(self.test_public_key_bytes)

if __name__ == '__main__':
    unittest.main()