from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from hmac import compare_digest
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_field_element import (
    Ed25519EncodedFieldElement,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field import (
    Ed25519Field,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field_element import (
    Ed25519FieldElement,
)


class Ed25519EncodedGroupElement:

    def __init__(self, values: bytes):
        if len(values) != 32:
            raise IllegalArgumentException("Invalid encoded group element.")
        self.values = values

    def get_raw(self) -> bytes:
        return self.values

    def decode(self):
        from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_group_element import (
            Ed25519GroupElement,
        )

        x = self.get_affine_x()
        y = self.get_affine_y()
        return Ed25519GroupElement.p3(x, y, Ed25519Field.ONE, x.multiply(y))

    @staticmethod
    def _get_array_bit(array: bytes, index: int) -> int:
        return (array[index >> 3] >> (index & 7)) & 1

    def get_affine_x(self):
        y = self.get_affine_y()
        y_square = y.square()

        u = y_square.subtract(Ed25519Field.ONE)

        v = y_square.multiply(Ed25519Field.D).add(Ed25519Field.ONE)

        x = Ed25519FieldElement.sqrt(u, v)

        vx_square = x.square().multiply(v)
        check_for_zero = vx_square.subtract(u)
        if check_for_zero.is_non_zero():
            check_for_zero = vx_square.add(u)
            if check_for_zero.is_non_zero():
                raise IllegalArgumentException(
                    "Not a valid Ed25519EncodedGroupElement."
                )

            x = x.multiply(Ed25519Field.I)

        if (1 if x.is_negative() else 0) != self._get_array_bit(self.values, 255):
            x = x.negate()

        return x

    def get_affine_y(self):
        encoded = Ed25519EncodedFieldElement(self.values)
        return encoded.decode()

    def __hash__(self):
        if self.values is None:
            return 0
        else:
            result = 1
            for element in self.values:
                result = 31 * result + element
            return result

    def __eq__(self, other):
        if not isinstance(other, Ed25519EncodedGroupElement):
            return False

        return compare_digest(self.values, other.values)

    def __str__(self):
        return "x={}\ny={}\n".format(self.get_affine_x(), self.get_affine_y())
