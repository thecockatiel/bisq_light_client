from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.bond.bonded_asset import BondedAsset


class Reputation(BondedAsset):
    """
    Reputation objects we found on the blockchain. We only know the hash of it.
    In contrast to MyReputation which represents the object we created and contains the
    private salt data.
    """

    def __init__(self, hash: bytes):
        self._hash = hash

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BondedAsset implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def hash(self):
        return self._hash

    @property
    def display_string(self):
        return self.uid

    @property
    def uid(self):
        return bytes_as_hex_string(self._hash)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Reputation):
            return False
        return self._hash == other._hash

    def __hash__(self):
        return hash(self._hash)

    def __str__(self):
        return (
            "Reputation{\n"  #
            f"     hash={bytes_as_hex_string(self._hash)}\n"
            "}"
        )
