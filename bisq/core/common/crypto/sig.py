import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.exceptions import InvalidSignature

from bisq.core.common.crypto.crypto_exception import CryptoException
from bisq.core.common.crypto.key_conversion_exception import KeyConversionException
from bisq.logging import get_logger

logger = get_logger(__name__)

class Sig:
    KEY_ALGO = "DSA"
    ALGO = "SHA256withDSA"

    @staticmethod
    def generate_key_pair():
        try:
            private_key = dsa.generate_private_key(key_size=1024)
            public_key = private_key.public_key()
            return (private_key, public_key)
        except ValueError as e:
            logger.error("Could not create key.", exc_info=True)
            raise RuntimeError("Could not create key.") from e

    @staticmethod
    def sign(private_key: dsa.DSAPrivateKey, data: bytes):
        try:
            signature = private_key.sign(
                data,
                hashes.SHA256()
            )
            return signature
        except Exception as e:
            raise CryptoException(f"Signing failed. {str(e)}") from e

    @staticmethod
    def sign_message(private_key: dsa.DSAPrivateKey, message: str):
        try:
            data = message.encode('utf-8')
            sig_bytes = Sig.sign(private_key, data)
            return base64.b64encode(sig_bytes).decode('utf-8')
        except Exception as e:
            raise CryptoException(f"Signing message failed. {str(e)}") from e

    @staticmethod
    def verify(public_key: dsa.DSAPublicKey, data: bytes, signature: bytes):
        try:
            public_key.verify(
                signature,
                data,
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            raise CryptoException("Signature verification failed") from e

    @staticmethod
    def verify_message(public_key: dsa.DSAPublicKey, message: str, signature_b64: str):
        try:
            data = message.encode('utf-8')
            signature = base64.b64decode(signature_b64)
            return Sig.verify(public_key, data, signature)
        except Exception as e:
            raise CryptoException(f"Verifying message failed. {str(e)}") from e

    @staticmethod
    def get_public_key_from_bytes(sig_public_key_bytes: bytes):
        try:
            public_key = serialization.load_der_public_key(sig_public_key_bytes)
            return public_key
        except Exception as e:
            logger.error(f"Error creating sigPublicKey from bytes. sigPublicKeyBytes as hex={sig_public_key_bytes.hex()}, error={e}", exc_info=True)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_public_key_bytes(sig_public_key: dsa.DSAPublicKey):
        try:
            return sig_public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        except Exception as e:
            logger.error("Error encoding public key to bytes.", exc_info=True)
            raise KeyConversionException(e) from e