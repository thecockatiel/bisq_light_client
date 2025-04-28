from pathlib import Path
from typing import TYPE_CHECKING, Union

from cryptography.hazmat.primitives import serialization
from bisq.common.crypto.key_entry import KeyEntry
from bisq.common.crypto.key_pair import KeyPair
from bisq.common.file.file_util import rolling_backup
from bisq.common.setup.log_setup import get_ctx_logger
from utils.dir import check_dir
from bisq.common.crypto.encryption import DSA, rsa, Encryption

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing

class KeyStorage:
    def __init__(self, storage_dir: Path):
        self.storage_dir = check_dir(storage_dir)
        self.logger = get_ctx_logger(__name__)

    def all_key_files_exist(self) -> bool:
        return all([self.storage_dir.joinpath(f"{entry.file_name}.key").exists() for entry in [KeyEntry.MSG_SIGNATURE, KeyEntry.MSG_ENCRYPTION]])

    def load_key_pair(self, key_entry: KeyEntry):
        rolling_backup(self.storage_dir, key_entry.file_name, 20)
        private_key = None
        public_key = None

        try:
            private_key_path = self.storage_dir.joinpath(f"{key_entry.file_name}.key")
            with open(private_key_path, 'rb') as f:
                encoded_private_key_data = f.read()
            if key_entry == KeyEntry.MSG_SIGNATURE:
                private_key = DSA.import_key(encoded_private_key_data)
                public_key = private_key.publickey()
            else:
                private_key = serialization.load_der_private_key(encoded_private_key_data, password=None)
                public_key = private_key.public_key()
            return KeyPair(private_key, public_key)
        except Exception as e:
            self.logger.error(f"Could not load key {key_entry}: {e}")
            raise RuntimeError(f"Could not load key {key_entry}: {e}") from e

    def save_key_ring(self, key_ring: 'KeyRing'):
        self.save_private_key(key_ring.signature_key_pair.private_key, KeyEntry.MSG_SIGNATURE.file_name)
        self.save_private_key(key_ring.encryption_key_pair.private_key, KeyEntry.MSG_ENCRYPTION.file_name)

    def save_private_key(self, private_key: Union[DSA.DsaKey, rsa.RSAPrivateKey], name: str):
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = self.storage_dir.joinpath(f"{name}.key")
        try:
            data = Encryption.get_private_key_bytes(private_key)
            with open(file_path, 'wb') as fos:
                fos.write(data)
        except Exception as e:
            self.logger.error(f"Could not save key {name}", exc_info=e)
            raise RuntimeError(f"Could not save key {name}", e) from e