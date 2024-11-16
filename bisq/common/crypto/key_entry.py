from enum import Enum

from bisq.common.crypto.encryption import Encryption
from bisq.common.crypto.sig import Sig


class KeyEntry(Enum):
    MSG_SIGNATURE = "sig", Sig.KEY_ALGO
    MSG_ENCRYPTION = "enc", Encryption.ASYM_KEY_ALGO

    def __init__(self, file_name: str, algorithm: str):
        self.file_name = file_name
        self.algorithm = algorithm

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def __str__(self):
        return f"KeyEntry(fileName='{self.file_name}', algorithm='{self.algorithm}')"
