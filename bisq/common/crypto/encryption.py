import base64
from io import BytesIO
import hmac
import hashlib
import secrets
from typing import TYPE_CHECKING, Union
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from electrum_min.crypto import sha256d
from electrum_min.ecc import ECPrivkey, ECPubkey, msg_magic, string_to_number
from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.key_conversion_exception import KeyConversionException
from bisq.common.crypto.key_pair import KeyPair
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string

if TYPE_CHECKING:
    try:
        from cryptography.hazmat.primitives.asymmetric.types import PUBLIC_KEY_TYPES, PRIVATE_KEY_TYPES
    except:
        # not available in old versions
        pass

logger = get_logger(__name__)

class Encryption:
    ASYM_KEY_ALGO = "RSA"
    ASYM_CIPHER = "RSA/ECB/OAEPWithSHA-256AndMGF1PADDING"

    SYM_KEY_ALGO = "AES"
    SYM_CIPHER = "AES"

    HMAC = "HmacSHA256"

    @staticmethod
    def generate_key_pair():
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            public_key = private_key.public_key()
            return KeyPair(private_key, public_key)
        except Exception as e:
            logger.error("Could not create key.", exc_info=e)
            raise RuntimeError("Could not create key.") from e

    ##########################################################################################
    # Symmetric
    ##########################################################################################

    @staticmethod
    def encrypt(payload: bytes, secret_key: bytes):
        try:
            cipher = Cipher(algorithms.AES(secret_key), mode=modes.ECB())
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(payload) + padder.finalize()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            return ciphertext
        except Exception as e:
            logger.error("error in encrypt", exc_info=e)
            raise CryptoException(e) from e

    @staticmethod
    def decrypt(encrypted_payload: bytes, secret_key: bytes):
        try:
            cipher = Cipher(algorithms.AES(secret_key), mode=modes.ECB())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_payload) + decryptor.finalize()
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data
        except Exception as e:
            raise CryptoException(e) from e

    ##########################################################################################
    # Hmac
    ##########################################################################################

    @staticmethod
    def get_payload_with_hmac(payload: bytes, secret_key: bytes) -> bytes:
        """Combine payload with its HMAC"""
        try:
            hmac_value = Encryption.get_hmac(payload, secret_key)
            with BytesIO() as output:
                output.write(payload)
                output.write(hmac_value)
                return output.getvalue()
        except Exception as e:
            logger.error("Could not create hmac", exc_info=e)
            raise RuntimeError("Could not create hmac") from e

    @staticmethod
    def verify_hmac(message: bytes, hmac_value: bytes, secret_key: bytes) -> bool:
        """Verify HMAC for given message"""
        try:
            hmac_test = Encryption.get_hmac(message, secret_key)
            return hmac.compare_digest(hmac_test, hmac_value)
        except Exception as e:
            logger.error("Could not verify hmac", exc_info=e)
            raise RuntimeError("Could not verify hmac") from e

    @staticmethod
    def get_hmac(payload: bytes, secret_key: bytes) -> bytes:
        """Generate HMAC for given payload and key"""
        h = hmac.HMAC(secret_key, payload, digestmod=hashlib.sha256)
        return h.digest()

    ##########################################################################################
    # Symmetric with Hmac
    ##########################################################################################
    @staticmethod
    def encrypt_payload_with_hmac(payload: bytes, secret_key: bytes):
        return Encryption.encrypt(Encryption.get_payload_with_hmac(payload, secret_key), secret_key)

    @staticmethod
    def decrypt_payload_with_hmac(encrypted_payload_with_hmac: bytes, secret_key: bytes):
        payload_with_hmac = Encryption.decrypt(encrypted_payload_with_hmac, secret_key)
        payload_with_hmac_hex = payload_with_hmac.hex()
        # first part is raw message
        sep = len(payload_with_hmac_hex) - 64
        payload_hex = payload_with_hmac_hex[:sep]
        payload_hex_bytes = bytes.fromhex(payload_hex)
        hmac_hex = payload_with_hmac_hex[sep:]
        if Encryption.verify_hmac(payload_hex_bytes, bytes.fromhex(hmac_hex), secret_key):
            return payload_hex_bytes
        else:
            raise CryptoException("Hmac does not match.")

    ##########################################################################################
    # Asymmetric
    ##########################################################################################
    @staticmethod
    def encrypt_secret_key(secret_key: bytes, public_key: rsa.RSAPublicKey):
        try:
            encrypted = public_key.encrypt(
                secret_key,
                rsa_padding.OAEP(
                    mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted
        except Exception as e:
            logger.error("Couldn't encrypt payload", exc_info=e)
            raise CryptoException("Couldn't encrypt payload") from e

    @staticmethod
    def decrypt_secret_key(encrypted_secret_key: bytes, private_key: rsa.RSAPrivateKey):
        try:
            decrypted = private_key.decrypt(
                encrypted_secret_key,
                rsa_padding.OAEP(
                    mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted
        except Exception as e:
            # errors when trying to decrypt foreign network_messages are normal
            raise CryptoException(e) from e

    ##########################################################################################
    # Hybrid with signature of asymmetric key
    ##########################################################################################
    @staticmethod
    def generate_secret_key(bits: int) -> bytes:
        try:
            if bits not in [128, 192, 256]:  # Standard AES key sizes
                raise ValueError("Key size must be 128, 192, or 256 bits")
                
            key_bytes = secrets.token_bytes(bits // 8)  # Convert bits to bytes
            return key_bytes
        except Exception as e:
            logger.error("Couldn't generate key", exc_info=e)
            raise RuntimeError("Couldn't generate key") from e

    @staticmethod
    def get_public_key_bytes(public_key: Union["PUBLIC_KEY_TYPES", "PRIVATE_KEY_TYPES", ECPubkey, ECPrivkey, bytes]) -> bytes:
        if isinstance(public_key, bytes):
            return public_key
        if isinstance(public_key, ECPubkey) or isinstance(public_key, ECPrivkey):
            return public_key.get_public_key_bytes()
        if hasattr(public_key, "public_key"):
            public_key = public_key.public_key() # in case we are passed a private key
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def get_public_key_from_bytes(public_key_bytes: bytes) -> rsa.RSAPublicKey:
        try:
            key = serialization.load_der_public_key(public_key_bytes)
            return key
        except Exception as e:
            logger.error(
                f"Error creating public key from bytes. Key bytes as hex={bytes_as_hex_string(public_key_bytes)}, error={str(e)}"
            )
            raise KeyConversionException(e) from e

    @staticmethod
    def get_private_key_from_bytes(private_key_bytes: bytes) -> rsa.RSAPublicKey:
        try:
            key = serialization.load_der_private_key(private_key_bytes, password=None)
            return key
        except Exception as e:
            logger.error(
                f"Error creating private key from bytes. Key bytes as hex=REDACTED, error={str(e)}"
            )
            raise KeyConversionException(e) from e

    ##########################################################################################
    # EC (bitcoinj compatibility layer) - LowRSigningKey
    ##########################################################################################
    
    @staticmethod
    def get_ec_private_key_from_int_hex_string(key: str) -> ECPrivkey:
        try:
            key = ECPrivkey.from_secret_scalar(string_to_number(bytes.fromhex(key)))
            return key
        except Exception as e:
            logger.error(
                f"Error creating private key from bytes. Key bytes as hex=REDACTED, error={str(e)}"
            )
            raise KeyConversionException(e) from e
    
    @staticmethod
    def get_ec_public_key_from_bytes(public_key_bytes: bytes) -> ECPubkey:
        try:
            key = ECPubkey(public_key_bytes)
            return key
        except Exception as e:
            logger.error(
                f"Error creating ec public key from bytes. Key bytes as hex={bytes_as_hex_string(public_key_bytes)}, error={str(e)}"
            )
            raise KeyConversionException(e) from e
    
    @staticmethod
    def verify_ec_message_is_from_pubkey(message: str, signature_base64: str, pubkey_bytes: bytes):
        sig_bytes = base64.b64decode(signature_base64)
        msg_hash = sha256d(msg_magic(message.encode('utf-8')))
        pubkey, _, __ = ECPubkey.from_signature65(sig_bytes, msg_hash)
        if pubkey.get_public_key_bytes() != pubkey_bytes:
            raise CryptoException("Signature is not from the given public key.")
        
    ##########################################################################################
    # Helpers
    ##########################################################################################
            
    @staticmethod
    def is_pubkeys_equal(key1: "PUBLIC_KEY_TYPES", key2: "PUBLIC_KEY_TYPES"):
        if isinstance(key1, ECPubkey) and isinstance(key2, ECPubkey):
            return key1 == key2
        return Encryption.get_public_key_bytes(key1) == Encryption.get_public_key_bytes(key2)
