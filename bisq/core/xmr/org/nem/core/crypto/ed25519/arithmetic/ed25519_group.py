from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_group_element import (
    Ed25519EncodedGroupElement,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field import (
    Ed25519Field,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_group_element import (
    Ed25519GroupElement,
)


class Ed25519Group:
    """Represents the underlying group for Ed25519."""

    @staticmethod
    def get_base_point() -> "Ed25519GroupElement":
        raw_encoded_group_element = bytes.fromhex(
            "5866666666666666666666666666666666666666666666666666666666666666"
        )
        base_point = Ed25519EncodedGroupElement(raw_encoded_group_element).decode()
        base_point.precompute_for_scalar_multiplication()
        base_point.precompute_for_double_scalar_multiplication()
        return base_point

    GROUP_ORDER = (1 << 252) + 27742317777372353535851937790883648493
    """2^252 - 27742317777372353535851937790883648493"""

    BASE_POINT: "Ed25519GroupElement" = None
    """(x, 4/5); x > 0"""

    # Different representations of zero
    ZERO_P3 = Ed25519GroupElement.p3(
        Ed25519Field.ZERO, Ed25519Field.ONE, Ed25519Field.ONE, Ed25519Field.ZERO
    )
    ZERO_P2 = Ed25519GroupElement.p2(
        Ed25519Field.ZERO, Ed25519Field.ONE, Ed25519Field.ONE
    )
    ZERO_PRECOMPUTED = Ed25519GroupElement.precomputed(
        Ed25519Field.ONE, Ed25519Field.ONE, Ed25519Field.ZERO
    )


Ed25519Group.BASE_POINT = Ed25519Group.get_base_point()
