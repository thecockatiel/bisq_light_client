from typing import TYPE_CHECKING, Optional
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.unsupported_operation_exception import (
    UnsupportedOperationException,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.coordinate_system import (
    CoordinateSystem,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_group_element import Ed25519EncodedGroupElement
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field import (
    Ed25519Field,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field_element import (
    Ed25519FieldElement,
)
from bisq.core.xmr.org.nem.core.utils.ed_byte_utils import EdByteUtils

if TYPE_CHECKING:
    from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_field_element import (
        Ed25519EncodedFieldElement,
    )


class Ed25519GroupElement:
    """
    A point on the ED25519 curve which represents a group element.

    This implementation is based on the ref10 implementation of SUPERCOP.
    """

    def __init__(
        self,
        coordinate_system: "CoordinateSystem",
        x: "Ed25519FieldElement",
        y: "Ed25519FieldElement",
        z: "Ed25519FieldElement",
        t: Optional["Ed25519FieldElement"],
    ):
        self.coordinate_system = coordinate_system
        self.x = x
        self.y = y
        self.z = z
        self.t = t
        self._precomputed_for_single: Optional[list[list[Ed25519GroupElement]]] = None
        self._precomputed_for_double: Optional[list[Ed25519GroupElement]] = None

    @staticmethod
    def p2(
        x: "Ed25519FieldElement",
        y: "Ed25519FieldElement",
        z: "Ed25519FieldElement",
    ):
        return Ed25519GroupElement(CoordinateSystem.P2, x, y, z, None)

    @staticmethod
    def p3(
        x: "Ed25519FieldElement",
        y: "Ed25519FieldElement",
        z: "Ed25519FieldElement",
        t: "Ed25519FieldElement",
    ):
        return Ed25519GroupElement(CoordinateSystem.P3, x, y, z, t)

    @staticmethod
    def p1xp1(
        x: "Ed25519FieldElement",
        y: "Ed25519FieldElement",
        z: "Ed25519FieldElement",
        t: "Ed25519FieldElement",
    ):
        return Ed25519GroupElement(CoordinateSystem.P1xP1, x, y, z, t)

    @staticmethod
    def precomputed(
        y_plus_x: "Ed25519FieldElement",
        y_minus_x: "Ed25519FieldElement",
        xy2d: "Ed25519FieldElement",
    ):
        return Ed25519GroupElement(
            CoordinateSystem.PRECOMPUTED, y_plus_x, y_minus_x, xy2d, None
        )

    @staticmethod
    def cached(
        y_plus_x: "Ed25519FieldElement",
        y_minus_x: "Ed25519FieldElement",
        z: "Ed25519FieldElement",
        T2d: "Ed25519FieldElement",
    ):
        return Ed25519GroupElement(CoordinateSystem.CACHED, y_plus_x, y_minus_x, z, T2d)

    def encode(self) -> "Ed25519EncodedGroupElement":
        if self.coordinate_system in {CoordinateSystem.P2, CoordinateSystem.P3}:
            inverse = self.z.invert()
            x = self.x.multiply(inverse)
            y = self.y.multiply(inverse)
            s = y.encode().get_raw()
            s[-1] |= 0x80 if x.is_negative() else 0x00
            return Ed25519EncodedGroupElement(s)
        else:
            return self.to_p2().encode()

    def to_p2(self):
        return self._to_coordinate_system(CoordinateSystem.P2)

    def to_p3(self):
        return self._to_coordinate_system(CoordinateSystem.P3)

    def to_cached(self):
        return self._to_coordinate_system(CoordinateSystem.CACHED)

    def _to_coordinate_system(self, new_coordinate_system: "CoordinateSystem"):
        if self.coordinate_system == CoordinateSystem.P2:
            if new_coordinate_system == CoordinateSystem.P2:
                return Ed25519GroupElement.p2(self.x, self.y, self.z)
            else:
                raise IllegalArgumentException("Invalid coordinate system transition")
        elif self.coordinate_system == CoordinateSystem.P3:
            if new_coordinate_system == CoordinateSystem.P2:
                return Ed25519GroupElement.p2(self.x, self.y, self.z)
            elif new_coordinate_system == CoordinateSystem.P3:
                return Ed25519GroupElement.p3(self.x, self.y, self.z, self.t)
            elif new_coordinate_system == CoordinateSystem.CACHED:
                return Ed25519GroupElement.cached(
                    self.y.add(self.x),
                    self.y.subtract(self.x),
                    self.z,
                    self.t.multiply(Ed25519Field.D_TIMES_TWO),
                )
            else:
                raise IllegalArgumentException("Invalid coordinate system transition")
        elif self.coordinate_system == CoordinateSystem.P1xP1:
            if new_coordinate_system == CoordinateSystem.P2:
                return Ed25519GroupElement.p2(
                    self.x.multiply(self.t),
                    self.y.multiply(self.z),
                    self.z.multiply(self.t),
                )
            elif new_coordinate_system == CoordinateSystem.P3:
                return Ed25519GroupElement.p3(
                    self.x.multiply(self.t),
                    self.y.multiply(self.z),
                    self.z.multiply(self.t),
                    self.x.multiply(self.y),
                )
            elif new_coordinate_system == CoordinateSystem.P1xP1:
                return Ed25519GroupElement.p1xp1(self.x, self.y, self.z, self.t)
            else:
                raise IllegalArgumentException("Invalid coordinate system transition")
        elif self.coordinate_system == CoordinateSystem.PRECOMPUTED:
            if new_coordinate_system == CoordinateSystem.PRECOMPUTED:
                return Ed25519GroupElement.precomputed(self.x, self.y, self.z)
            else:
                raise IllegalArgumentException("Invalid coordinate system transition")
        elif self.coordinate_system == CoordinateSystem.CACHED:
            if new_coordinate_system == CoordinateSystem.CACHED:
                return Ed25519GroupElement.cached(self.x, self.y, self.z, self.t)
            else:
                raise IllegalArgumentException("Invalid coordinate system transition")
        else:
            raise UnsupportedOperationException("Unsupported coordinate system")

    def precompute_for_scalar_multiplication(self):
        if self._precomputed_for_single is not None:
            return

        Bi = self
        self._precomputed_for_single = [[None for _ in range(8)] for _ in range(32)]

        for i in range(32):
            Bij = Bi
            for j in range(8):
                inverse = Bij.z.invert()
                x = Bij.x.multiply(inverse)
                y = Bij.y.multiply(inverse)
                self._precomputed_for_single[i][j] = Ed25519GroupElement.precomputed(
                    y.add(x),
                    y.subtract(x),
                    x.multiply(y).multiply(Ed25519Field.D_TIMES_TWO),
                )
                Bij = Bij.add(Bi.to_cached()).to_p3()
            # Only every second summand is precomputed (16^2 = 256).
            for _ in range(8):
                Bi = Bi.add(Bi.to_cached()).to_p3()

    def precompute_for_double_scalar_multiplication(self):
        if self._precomputed_for_double is not None:
            return

        Bi = self
        self._precomputed_for_double = [None for _ in range(8)]

        for i in range(8):
            inverse = Bi.z.invert()
            x = Bi.x.multiply(inverse)
            y = Bi.y.multiply(inverse)
            self._precomputed_for_double[i] = Ed25519GroupElement.precomputed(
                y.add(x),
                y.subtract(x),
                x.multiply(y).multiply(Ed25519Field.D_TIMES_TWO),
            )
            Bi = self.add(self.add(Bi.to_cached()).to_p3().to_cached()).to_p3()

    def dbl(self):
        if self.coordinate_system in {CoordinateSystem.P2, CoordinateSystem.P3}:
            x_square = self.x.square()
            y_square = self.y.square()
            b = self.z.square_and_double()
            a = self.x.add(self.y)
            a_square = a.square()
            y_square_plus_x_square = y_square.add(x_square)
            y_square_minus_x_square = y_square.subtract(x_square)
            return Ed25519GroupElement.p1xp1(
                a_square.subtract(y_square_plus_x_square),
                y_square_plus_x_square,
                y_square_minus_x_square,
                b.subtract(y_square_minus_x_square),
            )
        else:
            raise UnsupportedOperationException()

    def _precomputed_add(self, g: "Ed25519GroupElement") -> "Ed25519GroupElement":
        if self.coordinate_system != CoordinateSystem.P3:
            raise UnsupportedOperationException()
        if g.coordinate_system != CoordinateSystem.PRECOMPUTED:
            raise IllegalArgumentException()

        y_plus_x = self.y.add(self.x)
        y_minus_x = self.y.subtract(self.x)
        a = y_plus_x.multiply(g.x)
        b = y_minus_x.multiply(g.y)
        c = g.z.multiply(self.t)
        d = self.z.add(self.z)

        return Ed25519GroupElement.p1xp1(
            a.subtract(b), a.add(b), d.add(c), d.subtract(c)
        )

    def _precomputed_subtract(self, g: "Ed25519GroupElement") -> "Ed25519GroupElement":
        if self.coordinate_system != CoordinateSystem.P3:
            raise UnsupportedOperationException()
        if g.coordinate_system != CoordinateSystem.PRECOMPUTED:
            raise IllegalArgumentException()

        y_plus_x = self.y.add(self.x)
        y_minus_x = self.y.subtract(self.x)
        a = y_plus_x.multiply(g.y)
        b = y_minus_x.multiply(g.x)
        c = g.z.multiply(self.t)
        d = self.z.add(self.z)

        return Ed25519GroupElement.p1xp1(
            a.subtract(b), a.add(b), d.subtract(c), d.add(c)
        )

    def add(self, g: "Ed25519GroupElement") -> "Ed25519GroupElement":
        if self.coordinate_system != CoordinateSystem.P3:
            raise UnsupportedOperationException()
        if g.coordinate_system != CoordinateSystem.CACHED:
            raise IllegalArgumentException()

        y_plus_x = self.y.add(self.x)
        y_minus_x = self.y.subtract(self.x)
        a = y_plus_x.multiply(g.x)
        b = y_minus_x.multiply(g.y)
        c = g.t.multiply(self.t)
        z_square = self.z.multiply(g.z)
        d = z_square.add(z_square)

        return Ed25519GroupElement.p1xp1(
            a.subtract(b), a.add(b), d.add(c), d.subtract(c)
        )

    def subtract(self, g: "Ed25519GroupElement") -> "Ed25519GroupElement":
        if self.coordinate_system != CoordinateSystem.P3:
            raise UnsupportedOperationException()
        if g.coordinate_system != CoordinateSystem.CACHED:
            raise IllegalArgumentException()

        y_plus_x = self.y.add(self.x)
        y_minus_x = self.y.subtract(self.x)
        a = y_plus_x.multiply(g.y)
        b = y_minus_x.multiply(g.x)
        c = g.t.multiply(self.t)
        z_square = self.z.multiply(g.z)
        d = z_square.add(z_square)

        return Ed25519GroupElement.p1xp1(
            a.subtract(b), a.add(b), d.subtract(c), d.add(c)
        )

    def __hash__(self):
        return hash(self.encode())

    def __eq__(self, other):
        if not isinstance(other, Ed25519GroupElement):
            return False

        ge = other
        if self.coordinate_system != ge.coordinate_system:
            try:
                ge = ge._to_coordinate_system(self.coordinate_system)
            except Exception:
                return False

        if self.coordinate_system in {CoordinateSystem.P2, CoordinateSystem.P3}:
            if self.z == ge.z:
                return self.x == ge.x and self.y == ge.y

            x1 = self.x.multiply(ge.z)
            y1 = self.y.multiply(ge.z)
            x2 = ge.x.multiply(self.z)
            y2 = ge.y.multiply(self.z)

            return x1 == x2 and y1 == y2

        elif self.coordinate_system == CoordinateSystem.P1xP1:
            return self.to_p2() == ge

        elif self.coordinate_system == CoordinateSystem.PRECOMPUTED:
            return self.x == ge.x and self.y == ge.y and self.z == ge.z

        elif self.coordinate_system == CoordinateSystem.CACHED:
            if self.z == ge.z:
                return self.x == ge.x and self.y == ge.y and self.t == ge.t

            x3 = self.x.multiply(ge.z)
            y3 = self.y.multiply(ge.z)
            t3 = self.t.multiply(ge.z)
            x4 = ge.x.multiply(self.z)
            y4 = ge.y.multiply(self.z)
            t4 = ge.t.multiply(self.z)

            return x3 == x4 and y3 == y4 and t3 == t4

        return False

    @staticmethod
    def _to_radix16(encoded: "Ed25519EncodedFieldElement") -> list[int]:
        a = encoded.get_raw()
        e = [0] * 64
        for i in range(32):
            e[2 * i] = a[i] & 15
            e[2 * i + 1] = (a[i] >> 4) & 15
        # each e[i] is between 0 and 15
        # e[63] is between 0 and 7
        carry = 0
        for i in range(63):
            e[i] += carry
            carry = e[i] + 8
            carry >>= 4
            e[i] -= carry << 4
        e[63] += carry

        return e

    def _cmov(self, u: "Ed25519GroupElement", b: int) -> "Ed25519GroupElement":
        ret = None
        for _ in range(b):
            # Only for b == 1
            ret = u
        for _ in range(1 - b):
            # Only for b == 0
            ret = self
        return ret

    def _select(self, pos: int, b: int) -> "Ed25519GroupElement":
        from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_group import Ed25519Group
        
        b_negative = EdByteUtils.is_negative_constant_time(b)
        b_abs = b - (((-b_negative) & b) << 1)

        t = (
            Ed25519Group.ZERO_PRECOMPUTED
            ._cmov(
                self._precomputed_for_single[pos][0],
                EdByteUtils.is_equal_constant_time(b_abs, 1),
            )
            ._cmov(
                self._precomputed_for_single[pos][1],
                EdByteUtils.is_equal_constant_time(b_abs, 2),
            )
            ._cmov(
                self._precomputed_for_single[pos][2],
                EdByteUtils.is_equal_constant_time(b_abs, 3),
            )
            ._cmov(
                self._precomputed_for_single[pos][3],
                EdByteUtils.is_equal_constant_time(b_abs, 4),
            )
            ._cmov(
                self._precomputed_for_single[pos][4],
                EdByteUtils.is_equal_constant_time(b_abs, 5),
            )
            ._cmov(
                self._precomputed_for_single[pos][5],
                EdByteUtils.is_equal_constant_time(b_abs, 6),
            )
            ._cmov(
                self._precomputed_for_single[pos][6],
                EdByteUtils.is_equal_constant_time(b_abs, 7),
            )
            ._cmov(
                self._precomputed_for_single[pos][7],
                EdByteUtils.is_equal_constant_time(b_abs, 8),
            )
        )

        t_minus = Ed25519GroupElement.precomputed(t.y, t.x, t.z.negate())

        return t._cmov(t_minus, b_negative)

    def scalar_multiply(self, a: "Ed25519EncodedFieldElement") -> "Ed25519GroupElement":
        e = self._to_radix16(a)
        h = Ed25519GroupElement.p3(
            Ed25519Field.ZERO, Ed25519Field.ONE, Ed25519Field.ONE, Ed25519Field.ZERO
        )

        for i in range(1, 64, 2):
            g = self._select(i // 2, e[i])
            h = h._precomputed_add(g).to_p3()

        h = h.dbl().to_p2().dbl().to_p2().dbl().to_p2().dbl().to_p3()

        for i in range(0, 64, 2):
            g = self._select(i // 2, e[i])
            h = h._precomputed_add(g).to_p3()

        return h

    def __str__(self):
        return "X={}\nY={}\nZ={}\nT={}".format(self.x, self.y, self.z, self.t)
