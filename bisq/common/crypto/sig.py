import base64
from typing import Union

try:
    from Crypto.PublicKey import DSA
    from Crypto.Signature import DSS
    from Crypto.Hash import SHA256
except:
    # different name of pycryptodome on debian?
    from Cryptodome.PublicKey import DSA
    from Cryptodome.Signature import DSS
    from Cryptodome.Hash import SHA256

from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.key_conversion_exception import KeyConversionException
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string

logger = get_logger(__name__)


class PrehashedSha256:
    """a helper for DSS to use prehashed SHA256 data"""
    digest_size = 32
    block_size = 64
    oid = "2.16.840.1.101.3.4.2.1"
    
    def __init__(self, data: bytes):
        self.data = data
    
    def digest(self):
        return self.data
    
    def new(self, data: bytes):
        return SHA256.new(data)

class Sig:
    KEY_ALGO = "DSA"
    ALGO = "SHA256withDSA"

    @staticmethod
    def generate_key_pair():
        from bisq.common.crypto.key_pair import KeyPair
        try:
            private_key: DSA.DsaKey = DSA.generate(1024)
            public_key = private_key.publickey()
            return KeyPair(private_key, public_key)
        except Exception as e:
            logger.error("Could not create key.", exc_info=e)
            raise RuntimeError("Could not create key.") from e

    @staticmethod
    def sign(private_key: DSA.DsaKey, data: bytes):
        try:
            signer = DSS.new(private_key, 'deterministic-rfc6979', 'der')
            signature = signer.sign(
                SHA256.new(data),
            )
            return signature
        except Exception as e:
            raise CryptoException(f"Signing failed. {str(e)}") from e

    @staticmethod
    def sign_message(private_key: DSA.DsaKey, message: str):
        try:
            data = message.encode('utf-8')
            sig_bytes = Sig.sign(private_key, data)
            return base64.b64encode(sig_bytes).decode('utf-8')
        except Exception as e:
            raise CryptoException(f"Signing message failed. {str(e)}") from e

    @staticmethod
    def verify(public_key: DSA.DsaKey, data: bytes, signature: bytes):
        try:
            verifier = DSS.new(public_key, 'deterministic-rfc6979', 'der')
            verifier.verify(
                SHA256.new(data), 
                signature,
            )
            return True
        except ValueError:
            return False
        except Exception as e:
            raise CryptoException("Signature verification failed") from e

    @staticmethod
    def verify_message(public_key: DSA.DsaKey, message: str, signature_b64: str):
        try:
            data = message.encode('utf-8')
            signature = base64.b64decode(signature_b64)
            return Sig.verify(public_key, data, signature)
        except Exception as e:
            raise CryptoException(f"Verifying message failed. {str(e)}") from e

    @staticmethod
    def get_public_key_from_bytes(sig_public_key_bytes: bytes):
        try:
            public_key = DSA.import_key(sig_public_key_bytes)
            return public_key
        except Exception as e:
            logger.error(f"Error creating sigPublicKey from bytes. sigPublicKeyBytes as hex={bytes_as_hex_string(sig_public_key_bytes)}, error={e}", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_private_key_from_bytes(sig_private_key_bytes: bytes):
        try:
            private_key = DSA.import_key(sig_private_key_bytes)
            return private_key
        except Exception as e:
            logger.error(f"Error creating sigPublicKey from bytes. sigPublicKeyBytes as hex=REDACTED, error={e}", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_public_key_bytes(sig_public_key: DSA.DsaKey) -> bytes:
        try:
            return sig_public_key.publickey().export_key("DER")
        except Exception as e:
            logger.error("Error encoding public key to bytes.", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_private_key_bytes(sig_private_key: DSA.DsaKey) -> bytes:
        try:
            return sig_private_key.export_key("DER", pkcs8=True)
        except Exception as e:
            logger.error("Error encoding private key to bytes.", exc_info=e)
            raise KeyConversionException(e) from e

    @staticmethod
    def get_public_key_as_hex_string(sig_public_key: Union[DSA.DsaKey, bytes], allow_none: bool = False):
        if isinstance(sig_public_key, bytes):
            sig_public_key = Sig.get_public_key_from_bytes(sig_public_key)
        if not sig_public_key:
            if not allow_none:
                raise KeyConversionException("Public key is None.")
            return 'null'
        
        return Sig.get_public_key_bytes(sig_public_key).hex()

    @staticmethod
    def get_private_key_as_hex_string(sig_private_key: DSA.DsaKey, allow_none: bool = False):
        if not sig_private_key:
            if not allow_none:
                raise KeyConversionException("Private key is None.")
            return 'null'
        
        return Sig.get_private_key_bytes(sig_private_key).hex()