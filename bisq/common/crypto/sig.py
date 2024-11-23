import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.key_conversion_exception import KeyConversionException
from bisq.common.crypto.key_pair import KeyPair
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string

logger = get_logger(__name__)

class Sig:
    KEY_ALGO = "DSA"
    ALGO = "SHA256withDSA"

    @staticmethod
    def generate_key_pair():
        try:
            private_key = dsa.generate_private_key(key_size=1024, backend=default_backend())
            public_key = private_key.public_key()
            return KeyPair(private_key, public_key)
        except ValueError as e:
            logger.error("Could not create key.", exc_info=e)
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
            logger.error(f"Error creating sigPublicKey from bytes. sigPublicKeyBytes as hex={bytes_as_hex_string(sig_public_key_bytes)}, error={e}", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_private_key_from_bytes(sig_private_key_bytes: bytes):
        try:
            private_key = serialization.load_der_private_key(sig_private_key_bytes, password=None)
            return private_key
        except Exception as e:
            logger.error(f"Error creating sigPublicKey from bytes. sigPublicKeyBytes as hex=REDACTED, error={e}", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_public_key_bytes(sig_public_key: dsa.DSAPublicKey) -> bytes:
        try:
            return sig_public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        except Exception as e:
            logger.error("Error encoding public key to bytes.", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_private_key_bytes(sig_private_key: dsa.DSAPrivateKey) -> bytes:
        try:
            return sig_private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        except Exception as e:
            logger.error("Error encoding private key to bytes.", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_public_key_as_hex_string(sig_public_key: dsa.DSAPublicKey, allow_none: bool = False):
        if not sig_public_key:
            if not allow_none:
                raise KeyConversionException("Public key is None.")
            return 'null'
        
        return Sig.get_public_key_bytes(sig_public_key).hex()

    @staticmethod
    def get_private_key_as_hex_string(sig_private_key: dsa.DSAPrivateKey, allow_none: bool = False):
        if not sig_private_key:
            if not allow_none:
                raise KeyConversionException("Private key is None.")
            return 'null'
        
        return Sig.get_private_key_bytes(sig_private_key).hex()