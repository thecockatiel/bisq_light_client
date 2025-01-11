import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class MobileMessageEncryption:
    def __init__(self):
        self.key_spec: Optional[bytes] = None

    def set_key(self, key: str):
        encoded = key.encode("utf-8")
        if len(encoded) != 32:
            raise Exception("Key must be 32 bytes")
        self.key_spec = encoded

    def encrypt(self, value_to_encrypt: str, iv: str) -> str:
        # Pad the input string to be multiple of 16
        while len(value_to_encrypt) % 16 != 0:
            value_to_encrypt += " "

        if len(iv) != 16:
            raise Exception("iv not 16 characters")

        iv_spec = iv.encode("utf-8")
        encrypted_bytes = self._do_encrypt(value_to_encrypt, iv_spec)
        return base64.b64encode(encrypted_bytes).decode("utf-8")

    def _do_encrypt(self, text: str, iv_spec: bytes) -> bytes:
        if not text:
            raise Exception("Empty string")

        try:
            cipher = Cipher(algorithms.AES(self.key_spec), modes.CBC(iv_spec))
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(text.encode("utf-8")) + encryptor.finalize()
            return encrypted
        except Exception as e:
            raise Exception(f"[encrypt] {str(e)}")
