import os
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dsa, rsa
from cryptography.hazmat.backends import default_backend
from bisq.core.common.crypto.key_entry import KeyEntry
from bisq.core.common.crypto.key_pair import KeyPair
from bisq.core.common.file.file_util import rolling_backup
from bisq.core.common.setup.log_setup import get_logger
from utils.dir import check_dir

if TYPE_CHECKING:
    from bisq.core.common.crypto.key_ring import KeyRing

logger = get_logger(__name__)

class KeyStorage:
    def __init__(self, storage_dir: str):
        self.storage_dir = check_dir(storage_dir)

    def all_key_files_exist(self) -> bool:
        return all([os.path.exists(os.path.join(self.storage_dir, f"{entry.file_name}.key")) for entry in [KeyEntry.MSG_SIGNATURE, KeyEntry.MSG_ENCRYPTION]])

    def load_key_pair(self, key_entry: KeyEntry):
        rolling_backup(self.storage_dir, key_entry.file_name, 20)
        private_key = None
        public_key = None

        try:
            private_key_path = os.path.join(self.storage_dir, f"{key_entry.file_name}.key")
            with open(private_key_path, 'rb') as f:
                encoded_private_key_data = f.read()
                private_key = serialization.load_pem_private_key(encoded_private_key_data, password=None, backend=default_backend())
                public_key = private_key.public_key()
            return KeyPair(private_key, public_key)
        except Exception as e:
            logger.error(f"Could not load key {key_entry}: {e}")
            raise RuntimeError(f"Could not load key {key_entry}: {e}") from e

    def save_key_ring(self, key_ring: 'KeyRing'):
        self.save_private_key(key_ring.signature_key_pair.private_key, KeyEntry.MSG_SIGNATURE.file_name)
        self.save_private_key(key_ring.encryption_key_pair.private_key, KeyEntry.MSG_ENCRYPTION.file_name)

    def save_private_key(self, private_key: dsa.DSAPrivateKey | rsa.RSAPrivateKey, name: str):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
        
        file_path = os.path.join(self.storage_dir, f"{name}.key")
        try:
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(file_path, 'wb') as fos:
                fos.write(pem)
        except Exception as e:
            logger.error(f"Could not save key {name}", exc_info=e)
            raise RuntimeError(f"Could not save key {name}", e) from e