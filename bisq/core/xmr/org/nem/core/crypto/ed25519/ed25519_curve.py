from bisq.core.xmr.org.nem.core.crypto.curve import Curve
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_group import (
    Ed25519Group,
)


class Ed25519Curve(Curve):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Ed25519Curve, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_name(self):
        return "ed25519"

    def get_group_order(self):
        return Ed25519Group.GROUP_ORDER

    def get_half_group_order(self):
        return Ed25519Group.GROUP_ORDER >> 1

    @staticmethod
    def ed25519():
        """Gets the Ed25519 instance."""
        return Ed25519Curve()
