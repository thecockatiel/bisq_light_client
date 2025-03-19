from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_field_element import Ed25519EncodedFieldElement
from ctypes import c_int32, c_int64


class Ed25519FieldElement:
    """
    Represents a element of the finite field with p=2^255-19 elements.\n
    values[0] ... values[9], represent the integer\n
    values[0] + 2^26 * values[1] + 2^51 * values[2] + 2^77 * values[3] + 2^102 * values[4] + ... + 2^230 * values[9].\n
    Bounds on each values[i] vary depending on context.

    This implementation is based on the ref10 implementation of SUPERCOP.
    """

    def __init__(self, values: list[int]):
        if len(values) != 10:
            raise IllegalArgumentException("Invalid 2^25.5 bit representation.")

        self.values = values

    def get_raw(self):
        return self.values

    def is_non_zero(self) -> bool:
        return self.encode().is_non_zero()

    def add(self, g: "Ed25519FieldElement") -> "Ed25519FieldElement":
        g_values = g.values
        h = [c_int32(self.values[i] + g_values[i]).value for i in range(10)]
        return Ed25519FieldElement(h)

    def subtract(self, g: "Ed25519FieldElement") -> "Ed25519FieldElement":
        g_values = g.values
        h = [c_int32(self.values[i] - g_values[i]).value for i in range(10)]
        return Ed25519FieldElement(h)

    def negate(self) -> "Ed25519FieldElement":
        h = [-self.values[i] for i in range(10)]
        return Ed25519FieldElement(h)

    def multiply(self, g: "Ed25519FieldElement") -> "Ed25519FieldElement":
        g_values = g.values
        f = self.values
        f0, f1, f2, f3, f4, f5, f6, f7, f8, f9 = f
        g0, g1, g2, g3, g4, g5, g6, g7, g8, g9 = g_values
        g1_19, g2_19, g3_19, g4_19, g5_19, g6_19, g7_19, g8_19, g9_19 = [c_int32(19 * x).value for x in g_values[1:]]
        f1_2, f3_2, f5_2, f7_2, f9_2 = [c_int32(2 * x).value for x in f[1::2]]

        f0g0 = f0 * g0
        f0g1 = f0 * g1
        f0g2 = f0 * g2
        f0g3 = f0 * g3
        f0g4 = f0 * g4
        f0g5 = f0 * g5
        f0g6 = f0 * g6
        f0g7 = f0 * g7
        f0g8 = f0 * g8
        f0g9 = f0 * g9
        f1g0 = f1 * g0
        f1g1_2 = f1_2 * g1
        f1g2 = f1 * g2
        f1g3_2 = f1_2 * g3
        f1g4 = f1 * g4
        f1g5_2 = f1_2 * g5
        f1g6 = f1 * g6
        f1g7_2 = f1_2 * g7
        f1g8 = f1 * g8
        f1g9_19 = f1_2 * g9_19
        f2g0 = f2 * g0
        f2g1 = f2 * g1
        f2g2 = f2 * g2
        f2g3 = f2 * g3
        f2g4 = f2 * g4
        f2g5 = f2 * g5
        f2g6 = f2 * g6
        f2g7 = f2 * g7
        f2g8_19 = f2 * g8_19
        f2g9_19 = f2 * g9_19
        f3g0 = f3 * g0
        f3g1_2 = f3_2 * g1
        f3g2 = f3 * g2
        f3g3_2 = f3_2 * g3
        f3g4 = f3 * g4
        f3g5_2 = f3_2 * g5
        f3g6 = f3 * g6
        f3g7_19 = f3_2 * g7_19
        f3g8_19 = f3 * g8_19
        f3g9_19 = f3_2 * g9_19
        f4g0 = f4 * g0
        f4g1 = f4 * g1
        f4g2 = f4 * g2
        f4g3 = f4 * g3
        f4g4 = f4 * g4
        f4g5 = f4 * g5
        f4g6_19 = f4 * g6_19
        f4g7_19 = f4 * g7_19
        f4g8_19 = f4 * g8_19
        f4g9_19 = f4 * g9_19
        f5g0 = f5 * g0
        f5g1_2 = f5_2 * g1
        f5g2 = f5 * g2
        f5g3_2 = f5_2 * g3
        f5g4 = f5 * g4
        f5g5_19 = f5_2 * g5_19
        f5g6_19 = f5 * g6_19
        f5g7_19 = f5_2 * g7_19
        f5g8_19 = f5 * g8_19
        f5g9_19 = f5_2 * g9_19
        f6g0 = f6 * g0
        f6g1 = f6 * g1
        f6g2 = f6 * g2
        f6g3 = f6 * g3
        f6g4_19 = f6 * g4_19
        f6g5_19 = f6 * g5_19
        f6g6_19 = f6 * g6_19
        f6g7_19 = f6 * g7_19
        f6g8_19 = f6 * g8_19
        f6g9_19 = f6 * g9_19
        f7g0 = f7 * g0
        f7g1_2 = f7_2 * g1
        f7g2 = f7 * g2
        f7g3_19 = f7_2 * g3_19
        f7g4_19 = f7 * g4_19
        f7g5_19 = f7_2 * g5_19
        f7g6_19 = f7 * g6_19
        f7g7_19 = f7_2 * g7_19
        f7g8_19 = f7 * g8_19
        f7g9_19 = f7_2 * g9_19
        f8g0 = f8 * g0
        f8g1 = f8 * g1
        f8g2_19 = f8 * g2_19
        f8g3_19 = f8 * g3_19
        f8g4_19 = f8 * g4_19
        f8g5_19 = f8 * g5_19
        f8g6_19 = f8 * g6_19
        f8g7_19 = f8 * g7_19
        f8g8_19 = f8 * g8_19
        f8g9_19 = f8 * g9_19
        f9g0 = f9 * g0
        f9g1_19 = f9_2 * g1_19
        f9g2_19 = f9 * g2_19
        f9g3_19 = f9_2 * g3_19
        f9g4_19 = f9 * g4_19
        f9g5_19 = f9_2 * g5_19
        f9g6_19 = f9 * g6_19
        f9g7_19 = f9_2 * g7_19
        f9g8_19 = f9 * g8_19
        f9g9_19 = f9_2 * g9_19

        h0 = c_int64(f0g0 + f1g9_19 + f2g8_19 + f3g7_19 + f4g6_19 + f5g5_19 + f6g4_19 + f7g3_19 + f8g2_19 + f9g1_19).value
        h1 = c_int64(f0g1 + f1g0 + f2g9_19 + f3g8_19 + f4g7_19 + f5g6_19 + f6g5_19 + f7g4_19 + f8g3_19 + f9g2_19).value
        h2 = c_int64(f0g2 + f1g1_2 + f2g0 + f3g9_19 + f4g8_19 + f5g7_19 + f6g6_19 + f7g5_19 + f8g4_19 + f9g3_19).value
        h3 = c_int64(f0g3 + f1g2 + f2g1 + f3g0 + f4g9_19 + f5g8_19 + f6g7_19 + f7g6_19 + f8g5_19 + f9g4_19).value
        h4 = c_int64(f0g4 + f1g3_2 + f2g2 + f3g1_2 + f4g0 + f5g9_19 + f6g8_19 + f7g7_19 + f8g6_19 + f9g5_19).value
        h5 = c_int64(f0g5 + f1g4 + f2g3 + f3g2 + f4g1 + f5g0 + f6g9_19 + f7g8_19 + f8g7_19 + f9g6_19).value
        h6 = c_int64(f0g6 + f1g5_2 + f2g4 + f3g3_2 + f4g2 + f5g1_2 + f6g0 + f7g9_19 + f8g8_19 + f9g7_19).value
        h7 = c_int64(f0g7 + f1g6 + f2g5 + f3g4 + f4g3 + f5g2 + f6g1 + f7g0 + f8g9_19 + f9g8_19).value
        h8 = c_int64(f0g8 + f1g7_2 + f2g6 + f3g5_2 + f4g4 + f5g3_2 + f6g2 + f7g1_2 + f8g0 + f9g9_19).value
        h9 = c_int64(f0g9 + f1g8 + f2g7 + f3g6 + f4g5 + f5g4 + f6g3 + f7g2 + f8g1 + f9g0).value

        carry = [0] * 10
        carry[0] = (h0 + (1 << 25)) >> 26
        h1 += carry[0]
        h0 -= carry[0] << 26
        carry[4] = (h4 + (1 << 25)) >> 26
        h5 += carry[4]
        h4 -= carry[4] << 26

        carry[1] = (h1 + (1 << 24)) >> 25
        h2 += carry[1]
        h1 -= carry[1] << 25
        carry[5] = (h5 + (1 << 24)) >> 25
        h6 += carry[5]
        h5 -= carry[5] << 25

        carry[2] = (h2 + (1 << 25)) >> 26
        h3 += carry[2]
        h2 -= carry[2] << 26
        carry[6] = (h6 + (1 << 25)) >> 26
        h7 += carry[6]
        h6 -= carry[6] << 26

        carry[3] = (h3 + (1 << 24)) >> 25
        h4 += carry[3]
        h3 -= carry[3] << 25
        carry[7] = (h7 + (1 << 24)) >> 25
        h8 += carry[7]
        h7 -= carry[7] << 25

        carry[4] = (h4 + (1 << 25)) >> 26
        h5 += carry[4]
        h4 -= carry[4] << 26
        carry[8] = (h8 + (1 << 25)) >> 26
        h9 += carry[8]
        h8 -= carry[8] << 26

        carry[9] = (h9 + (1 << 24)) >> 25
        h0 += carry[9] * 19
        h9 -= carry[9] << 25

        carry[0] = (h0 + (1 << 25)) >> 26
        h1 += carry[0]
        h0 -= carry[0] << 26

        h = [c_int32(h0).value, c_int32(h1).value, c_int32(h2).value, c_int32(h3).value,
             c_int32(h4).value, c_int32(h5).value, c_int32(h6).value, c_int32(h7).value,
             c_int32(h8).value, c_int32(h9).value]
        return Ed25519FieldElement(h)

    def square(self) -> "Ed25519FieldElement":
        return self._square_and_optional_double(False)

    def square_and_double(self) -> "Ed25519FieldElement":
        return self._square_and_optional_double(True)

    def _square_and_optional_double(self, dbl: bool) -> "Ed25519FieldElement":
        f = self.values
        f0, f1, f2, f3, f4, f5, f6, f7, f8, f9 = f
        f0_2, f1_2, f2_2, f3_2, f4_2, f5_2, f6_2, f7_2 = [c_int32(2 * x).value for x in f[:8]]
        f5_38, f6_19, f7_38, f8_19, f9_38 = [c_int32(38 * f5).value, c_int32(19 * f6).value, c_int32(38 * f7).value, c_int32(19 * f8).value, c_int32(38 * f9).value]

        f0f0 = f0 * f0
        f0f1_2 = f0_2 * f1
        f0f2_2 = f0_2 * f2
        f0f3_2 = f0_2 * f3
        f0f4_2 = f0_2 * f4
        f0f5_2 = f0_2 * f5
        f0f6_2 = f0_2 * f6
        f0f7_2 = f0_2 * f7
        f0f8_2 = f0_2 * f8
        f0f9_2 = f0_2 * f9
        f1f1_2 = f1_2 * f1
        f1f2_2 = f1_2 * f2
        f1f3_4 = f1_2 * f3_2
        f1f4_2 = f1_2 * f4
        f1f5_4 = f1_2 * f5_2
        f1f6_2 = f1_2 * f6
        f1f7_4 = f1_2 * f7_2
        f1f8_2 = f1_2 * f8
        f1f9_76 = f1_2 * f9_38
        f2f2 = f2 * f2
        f2f3_2 = f2_2 * f3
        f2f4_2 = f2_2 * f4
        f2f5_2 = f2_2 * f5
        f2f6_2 = f2_2 * f6
        f2f7_2 = f2_2 * f7
        f2f8_38 = f2_2 * f8_19
        f2f9_38 = f2 * f9_38
        f3f3_2 = f3_2 * f3
        f3f4_2 = f3_2 * f4
        f3f5_4 = f3_2 * f5_2
        f3f6_2 = f3_2 * f6
        f3f7_76 = f3_2 * f7_38
        f3f8_38 = f3_2 * f8_19
        f3f9_76 = f3_2 * f9_38
        f4f4 = f4 * f4
        f4f5_2 = f4_2 * f5
        f4f6_38 = f4_2 * f6_19
        f4f7_38 = f4 * f7_38
        f4f8_38 = f4_2 * f8_19
        f4f9_38 = f4 * f9_38
        f5f5_38 = f5 * f5_38
        f5f6_38 = f5_2 * f6_19
        f5f7_76 = f5_2 * f7_38
        f5f8_38 = f5_2 * f8_19
        f5f9_76 = f5_2 * f9_38
        f6f6_19 = f6 * f6_19
        f6f7_38 = f6 * f7_38
        f6f8_38 = f6_2 * f8_19
        f6f9_38 = f6 * f9_38
        f7f7_38 = f7 * f7_38
        f7f8_38 = f7_2 * f8_19
        f7f9_76 = f7_2 * f9_38
        f8f8_19 = f8 * f8_19
        f8f9_38 = f8 * f9_38
        f9f9_38 = f9 * f9_38

        h0 = c_int64(f0f0 + f1f9_76 + f2f8_38 + f3f7_76 + f4f6_38 + f5f5_38).value
        h1 = c_int64(f0f1_2 + f2f9_38 + f3f8_38 + f4f7_38 + f5f6_38).value
        h2 = c_int64(f0f2_2 + f1f1_2 + f3f9_76 + f4f8_38 + f5f7_76 + f6f6_19).value
        h3 = c_int64(f0f3_2 + f1f2_2 + f4f9_38 + f5f8_38 + f6f7_38).value
        h4 = c_int64(f0f4_2 + f1f3_4 + f2f2 + f5f9_76 + f6f8_38 + f7f7_38).value
        h5 = c_int64(f0f5_2 + f1f4_2 + f2f3_2 + f6f9_38 + f7f8_38).value
        h6 = c_int64(f0f6_2 + f1f5_4 + f2f4_2 + f3f3_2 + f7f9_76 + f8f8_19).value
        h7 = c_int64(f0f7_2 + f1f6_2 + f2f5_2 + f3f4_2 + f8f9_38).value
        h8 = c_int64(f0f8_2 + f1f7_4 + f2f6_2 + f3f5_4 + f4f4 + f9f9_38).value
        h9 = c_int64(f0f9_2 + f1f8_2 + f2f7_2 + f3f6_2 + f4f5_2).value

        if dbl:
            h0 *= 2
            h1 *= 2
            h2 *= 2
            h3 *= 2
            h4 *= 2
            h5 *= 2
            h6 *= 2
            h7 *= 2
            h8 *= 2
            h9 *= 2

        carry = [0] * 10
        carry[0] = (h0 + (1 << 25)) >> 26
        h1 += carry[0]
        h0 -= carry[0] << 26
        carry[4] = (h4 + (1 << 25)) >> 26
        h5 += carry[4]
        h4 -= carry[4] << 26

        carry[1] = (h1 + (1 << 24)) >> 25
        h2 += carry[1]
        h1 -= carry[1] << 25
        carry[5] = (h5 + (1 << 24)) >> 25
        h6 += carry[5]
        h5 -= carry[5] << 25

        carry[2] = (h2 + (1 << 25)) >> 26
        h3 += carry[2]
        h2 -= carry[2] << 26
        carry[6] = (h6 + (1 << 25)) >> 26
        h7 += carry[6]
        h6 -= carry[6] << 26

        carry[3] = (h3 + (1 << 24)) >> 25
        h4 += carry[3]
        h3 -= carry[3] << 25
        carry[7] = (h7 + (1 << 24)) >> 25
        h8 += carry[7]
        h7 -= carry[7] << 25

        carry[4] = (h4 + (1 << 25)) >> 26
        h5 += carry[4]
        h4 -= carry[4] << 26
        carry[8] = (h8 + (1 << 25)) >> 26
        h9 += carry[8]
        h8 -= carry[8] << 26

        carry[9] = (h9 + (1 << 24)) >> 25
        h0 += carry[9] * 19
        h9 -= carry[9] << 25

        carry[0] = (h0 + (1 << 25)) >> 26
        h1 += carry[0]
        h0 -= carry[0] << 26

        h = [c_int32(h0).value, c_int32(h1).value, c_int32(h2).value, c_int32(h3).value,
             c_int32(h4).value, c_int32(h5).value, c_int32(h6).value, c_int32(h7).value,
             c_int32(h8).value, c_int32(h9).value]
        return Ed25519FieldElement(h)

    def invert(self) -> "Ed25519FieldElement":
        f0 = self.square()
        f1 = self._pow2to9()
        f0 = f0.multiply(f1)
        f1 = self._pow2to252sub4()
        for _ in range(1, 4):
            f1 = f1.square()
        return f1.multiply(f0)
    
    def _pow2to9(self) -> "Ed25519FieldElement":
        f = self.square()
        f = f.square()
        f = f.square()
        return self.multiply(f)
    
    def _pow2to252sub4(self) -> "Ed25519FieldElement":
        f0 = self.square()
        f1 = self._pow2to9()
        f0 = f0.multiply(f1)
        f0 = f0.square()
        f0 = f1.multiply(f0)
        f1 = f0.square()
        for _ in range(1, 5):
            f1 = f1.square()
        f0 = f1.multiply(f0)
        f1 = f0.square()
        for _ in range(1, 10):
            f1 = f1.square()
        f1 = f1.multiply(f0)
        f2 = f1.square()
        for _ in range(1, 20):
            f2 = f2.square()
        f1 = f2.multiply(f1)
        f1 = f1.square()
        for _ in range(1, 10):
            f1 = f1.square()
        f0 = f1.multiply(f0)
        f1 = f0.square()
        for _ in range(1, 50):
            f1 = f1.square()
        f1 = f1.multiply(f0)
        f2 = f1.square()
        for _ in range(1, 100):
            f2 = f2.square()
        f1 = f2.multiply(f1)
        f1 = f1.square()
        for _ in range(1, 50):
            f1 = f1.square()
        f0 = f1.multiply(f0)
        f0 = f0.square()
        return f0.square()
    
    @staticmethod
    def sqrt(u: "Ed25519FieldElement", v: "Ed25519FieldElement") -> "Ed25519FieldElement":
        v3 = v.square().multiply(v)
        x = v3.square().multiply(v).multiply(u)
        x = x._pow2to252sub4().multiply(x)
        x = v3.multiply(u).multiply(x)
        return x
    
    def _mod_p(self) -> "Ed25519FieldElement":
        h = self.values[:]
        h0, h1, h2, h3, h4, h5, h6, h7, h8, h9 = h

        # Calculate q
        q = c_int32(19 * h9 + (1 << 24)).value >> 25
        q = c_int32(h0 + q).value >> 26
        q = c_int32(h1 + q).value >> 25
        q = c_int32(h2 + q).value >> 26
        q = c_int32(h3 + q).value >> 25
        q = c_int32(h4 + q).value >> 26
        q = c_int32(h5 + q).value >> 25
        q = c_int32(h6 + q).value >> 26
        q = c_int32(h7 + q).value >> 25
        q = c_int32(h8 + q).value >> 26
        q = c_int32(h9 + q).value >> 25

        # r = h - q * p = h - 2^255 * q + 19 * q
        # First add 19 * q then discard the bit 255
        h0 = c_int32(h0 + 19 * q).value

        carry0 = h0 >> 26
        h1 = c_int32(h1 + carry0).value
        h0 -= carry0 << 26
        carry1 = h1 >> 25
        h2 = c_int32(h2 + carry1).value
        h1 -= carry1 << 25
        carry2 = h2 >> 26
        h3 = c_int32(h3 + carry2).value
        h2 -= carry2 << 26
        carry3 = h3 >> 25
        h4 = c_int32(h4 + carry3).value
        h3 -= carry3 << 25
        carry4 = h4 >> 26
        h5 = c_int32(h5 + carry4).value
        h4 -= carry4 << 26
        carry5 = h5 >> 25
        h6 = c_int32(h6 + carry5).value
        h5 -= carry5 << 25
        carry6 = h6 >> 26
        h7 = c_int32(h7 + carry6).value
        h6 -= carry6 << 26
        carry7 = h7 >> 25
        h8 = c_int32(h8 + carry7).value
        h7 -= carry7 << 25
        carry8 = h8 >> 26
        h9 = c_int32(h9 + carry8).value
        h8 -= carry8 << 26
        carry9 = h9 >> 25
        h9 -= carry9 << 25

        h = [c_int32(h0).value, c_int32(h1).value, c_int32(h2).value, c_int32(h3).value,
             c_int32(h4).value, c_int32(h5).value, c_int32(h6).value, c_int32(h7).value,
             c_int32(h8).value, c_int32(h9).value]

        return Ed25519FieldElement(h)
    
    def encode(self) -> "Ed25519EncodedFieldElement":
        g = self._mod_p()
        g_values = g.values
        h0, h1, h2, h3, h4, h5, h6, h7, h8, h9 = g_values

        s = bytearray(32)
        s[0] = h0 & 0xFF
        s[1] = (h0 >> 8) & 0xFF
        s[2] = (h0 >> 16) & 0xFF
        s[3] = ((h0 >> 24) | (h1 << 2)) & 0xFF
        s[4] = (h1 >> 6) & 0xFF
        s[5] = (h1 >> 14) & 0xFF
        s[6] = ((h1 >> 22) | (h2 << 3)) & 0xFF
        s[7] = (h2 >> 5) & 0xFF
        s[8] = (h2 >> 13) & 0xFF
        s[9] = ((h2 >> 21) | (h3 << 5)) & 0xFF
        s[10] = (h3 >> 3) & 0xFF
        s[11] = (h3 >> 11) & 0xFF
        s[12] = ((h3 >> 19) | (h4 << 6)) & 0xFF
        s[13] = (h4 >> 2) & 0xFF
        s[14] = (h4 >> 10) & 0xFF
        s[15] = (h4 >> 18) & 0xFF
        s[16] = h5 & 0xFF
        s[17] = (h5 >> 8) & 0xFF
        s[18] = (h5 >> 16) & 0xFF
        s[19] = ((h5 >> 24) | (h6 << 1)) & 0xFF
        s[20] = (h6 >> 7) & 0xFF
        s[21] = (h6 >> 15) & 0xFF
        s[22] = ((h6 >> 23) | (h7 << 3)) & 0xFF
        s[23] = (h7 >> 5) & 0xFF
        s[24] = (h7 >> 13) & 0xFF
        s[25] = ((h7 >> 21) | (h8 << 4)) & 0xFF
        s[26] = (h8 >> 4) & 0xFF
        s[27] = (h8 >> 12) & 0xFF
        s[28] = ((h8 >> 20) | (h9 << 6)) & 0xFF
        s[29] = (h9 >> 2) & 0xFF
        s[30] = (h9 >> 10) & 0xFF
        s[31] = (h9 >> 18) & 0xFF

        return Ed25519EncodedFieldElement(s)

    def is_negative(self) -> bool:
        return self.encode().is_negative()

    def hash_code(self):
        if self.values is None:
            return 0
        else:
            result = 1
            for element in self.values:
                result = 31 * result + element
            return result

    def __hash__(self):
        return self.hash_code()

    def __eq__(self, obj):
        if not isinstance(obj, Ed25519FieldElement):
            return False

        return self.encode() == obj.encode()

    def __str__(self):
        return str(self.encode())
