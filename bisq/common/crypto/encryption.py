from io import BytesIO
import hmac as builtin_hmac
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hmac, padding, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding, ec
from cryptography.hazmat.backends import default_backend
from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.key_conversion_exception import KeyConversionException
from bisq.common.crypto.key_pair import KeyPair
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string

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
                backend=default_backend()
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
            cipher = Cipher(algorithms.AES(secret_key), mode=modes.ECB(), backend=default_backend())
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
            cipher = Cipher(algorithms.AES(secret_key), mode=modes.ECB(), backend=default_backend())
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
            return builtin_hmac.compare_digest(hmac_test, hmac_value)
        except Exception as e:
            logger.error("Could not verify hmac", exc_info=e)
            raise RuntimeError("Could not verify hmac") from e

    @staticmethod
    def get_hmac(payload: bytes, secret_key: bytes) -> bytes:
        """Generate HMAC for given payload and key"""
        h = hmac.HMAC(secret_key, hashes.SHA256(), backend=default_backend())
        h.update(payload)
        return h.finalize()

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
    def get_public_key_bytes(public_key: rsa.RSAPublicKey) -> bytes:
        return public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def get_public_key_from_bytes(public_key_bytes: bytes) -> rsa.RSAPublicKey:
        try:
            key = serialization.load_der_public_key(public_key_bytes, backend=default_backend())
            return key
        except Exception as e:
            logger.error(
                f"Error creating public key from bytes. Key bytes as hex={bytes_as_hex_string(public_key_bytes)}, error={str(e)}"
            )
            raise KeyConversionException(e) from e

    @staticmethod
    def get_private_key_from_bytes(private_key_bytes: bytes) -> rsa.RSAPublicKey:
        try:
            key = serialization.load_der_private_key(private_key_bytes, password=None, backend=default_backend())
            return key
        except Exception as e:
            logger.error(
                f"Error creating private key from bytes. Key bytes as hex=REDACTED, error={str(e)}"
            )
            raise KeyConversionException(e) from e

    ##########################################################################################
    # EC
    ##########################################################################################
    
    @staticmethod
    def get_ec_private_key_from_bytes(private_key_bytes: bytes) -> ec.EllipticCurvePrivateKey:
        try:
            key = ec.derive_private_key(int.from_bytes(private_key_bytes, byteorder='big'), ec.SECP256K1(), default_backend())
            return key
        except Exception as e:
            logger.error(
                f"Error creating private key from bytes. Key bytes as hex=REDACTED, error={str(e)}"
            )
            raise KeyConversionException(e) from e
    
    @staticmethod
    def get_ec_public_key_from_private_key(private_key: ec.EllipticCurvePrivateKey) -> bytes:
        try:
            public_pytes = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.CompressedPoint
            )
            return public_pytes
        except Exception as e:
            logger.error(
                f"Error creating bytes from ec private key. Key bytes as hex=REDACTED, error={str(e)}"
            )
            raise KeyConversionException(e) from e