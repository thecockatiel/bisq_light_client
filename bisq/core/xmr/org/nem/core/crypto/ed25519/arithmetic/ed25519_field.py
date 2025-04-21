from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_field_element import (
    Ed25519EncodedFieldElement,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field_element import (
    Ed25519FieldElement,
)


class Ed25519Field:
    """
    Represents the underlying finite field for Ed25519.
    The field has p = 2^255 - 19 elements.
    """

    P = int.from_bytes(
        bytes.fromhex(
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffed"
        ),
        byteorder="big",
    )
    """P: 2^255 - 19"""

    @staticmethod
    def _get_field_element(value: int) -> Ed25519FieldElement:
        f = [0] * 10
        f[0] = value
        return Ed25519FieldElement(f)

    @staticmethod
    def _get_d() -> Ed25519FieldElement:
        """
        Returns the constant 'd' used in the Ed25519 curve equation.
        """
        d = (-121665 * pow(121666, -1, Ed25519Field.P)) % Ed25519Field.P
        return Ed25519EncodedFieldElement(d.to_bytes(32, byteorder="little")).decode()

    ZERO: "Ed25519FieldElement" = None
    ONE: "Ed25519FieldElement" = None
    TWO: "Ed25519FieldElement" = None
    D: "Ed25519FieldElement" = None
    D_TIMES_TWO: "Ed25519FieldElement" = None
    ZERO_SHORT = bytes(32)
    ZERO_LONG = bytes(64)

    I = Ed25519EncodedFieldElement(
        bytes.fromhex(
            "b0a00e4a271beec478e42fad0618432fa7d7fb3d99004d2b0bdfc14f8024832b"
        )
    ).decode()
    """I ^ 2 = -1"""


Ed25519Field.ZERO = Ed25519Field._get_field_element(0)
Ed25519Field.ONE = Ed25519Field._get_field_element(1)
Ed25519Field.TWO = Ed25519Field._get_field_element(2)
Ed25519Field.D = Ed25519Field._get_d()
Ed25519Field.D_TIMES_TWO = Ed25519Field.D.multiply(Ed25519Field.TWO)
