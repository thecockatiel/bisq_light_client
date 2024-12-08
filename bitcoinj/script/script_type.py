from enum import Enum


class ScriptType(Enum):
    P2PKH = 1  # pay to pubkey hash (aka pay to address)
    P2PK = 2  # pay to pubkey
    P2SH = 3  # pay to script hash
    P2WPKH = 4  # pay to witness pubkey hash
    P2WSH = 5  # pay to witness script hash

    def __init__(self, id: int):
        self.id = id

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __str__(self):
        return f"ScriptType(id='{self.id}', name='{self.name}')"
