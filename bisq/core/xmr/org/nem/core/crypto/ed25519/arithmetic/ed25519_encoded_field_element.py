from ctypes import c_int64, c_int32
from typing import TYPE_CHECKING
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from hmac import compare_digest

if TYPE_CHECKING:
    from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field_element import (
        Ed25519FieldElement,
    )


class Ed25519EncodedFieldElement:
    """
    Represents a field element of the finite field with p=2^255-19 elements.
    The value of the field element is held in 2^8 bit representation, i.e. in a byte array.
    The length of the array must be 32 or 64.
    """

    def __init__(self, values: bytes):
        """
        Creates a new encoded field element.

        :param values: The byte array that holds the values.
        :raises ValueError: If the length of the byte array is not 32 or 64.
        """
        if len(values) == 32:
            self.zero = bytes(32)  # Ed25519Field.ZERO_SHORT
        elif len(values) == 64:
            self.zero = bytes(64)  # Ed25519Field.ZERO_LONG
        else:
            raise IllegalArgumentException("Invalid 2^8 bit representation.")

        self.values = values

    def get_raw(self):
        return self.values

    def is_negative(self):
        return (self.values[0] & 1) != 0

    def is_non_zero(self):
        return not compare_digest(self.values, self.zero)

    def decode(self) -> "Ed25519FieldElement":
        from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_field_element import (
            Ed25519FieldElement,
        )
        h0 = self._four_bytes_to_long(self.values, 0)
        h1 = self._three_bytes_to_long(self.values, 4) << 6
        h2 = self._three_bytes_to_long(self.values, 7) << 5
        h3 = self._three_bytes_to_long(self.values, 10) << 3
        h4 = self._three_bytes_to_long(self.values, 13) << 2
        h5 = self._four_bytes_to_long(self.values, 16)
        h6 = self._three_bytes_to_long(self.values, 20) << 7
        h7 = self._three_bytes_to_long(self.values, 23) << 5
        h8 = self._three_bytes_to_long(self.values, 26) << 4
        h9 = (self._three_bytes_to_long(self.values, 29) & 0x7FFFFF) << 2

        carry9 = (h9 + (1 << 24)) >> 25
        h0 += carry9 * 19
        h9 -= carry9 << 25
        carry1 = (h1 + (1 << 24)) >> 25
        h2 += carry1
        h1 -= carry1 << 25
        carry3 = (h3 + (1 << 24)) >> 25
        h4 += carry3
        h3 -= carry3 << 25
        carry5 = (h5 + (1 << 24)) >> 25
        h6 += carry5
        h5 -= carry5 << 25
        carry7 = (h7 + (1 << 24)) >> 25
        h8 += carry7
        h7 -= carry7 << 25

        carry0 = (h0 + (1 << 25)) >> 26
        h1 += carry0
        h0 -= carry0 << 26
        carry2 = (h2 + (1 << 25)) >> 26
        h3 += carry2
        h2 -= carry2 << 26
        carry4 = (h4 + (1 << 25)) >> 26
        h5 += carry4
        h4 -= carry4 << 26
        carry6 = (h6 + (1 << 25)) >> 26
        h7 += carry6
        h6 -= carry6 << 26
        carry8 = (h8 + (1 << 25)) >> 26
        h9 += carry8
        h8 -= carry8 << 26

        h = [0] * 10
        h[0] = c_int32(h0).value
        h[1] = c_int32(h1).value
        h[2] = c_int32(h2).value
        h[3] = c_int32(h3).value
        h[4] = c_int32(h4).value
        h[5] = c_int32(h5).value
        h[6] = c_int32(h6).value
        h[7] = c_int32(h7).value
        h[8] = c_int32(h8).value
        h[9] = c_int32(h9).value

        return Ed25519FieldElement(h)
    
    def mod_q(self) -> "Ed25519EncodedFieldElement":
        s0 = 0x1FFFFF & self._three_bytes_to_long(self.values, 0)
        s1 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 2) >> 5)
        s2 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 5) >> 2)
        s3 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 7) >> 7)
        s4 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 10) >> 4)
        s5 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 13) >> 1)
        s6 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 15) >> 6)
        s7 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 18) >> 3)
        s8 = 0x1FFFFF & self._three_bytes_to_long(self.values, 21)
        s9 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 23) >> 5)
        s10 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 26) >> 2)
        s11 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 28) >> 7)
        s12 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 31) >> 4)
        s13 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 34) >> 1)
        s14 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 36) >> 6)
        s15 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 39) >> 3)
        s16 = 0x1FFFFF & self._three_bytes_to_long(self.values, 42)
        s17 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 44) >> 5)
        s18 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 47) >> 2)
        s19 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 49) >> 7)
        s20 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 52) >> 4)
        s21 = 0x1FFFFF & (self._three_bytes_to_long(self.values, 55) >> 1)
        s22 = 0x1FFFFF & (self._four_bytes_to_long(self.values, 57) >> 6)
        s23 = self._four_bytes_to_long(self.values, 60) >> 3

        s11 += s23 * 666643
        s12 += s23 * 470296
        s13 += s23 * 654183
        s14 -= s23 * 997805
        s15 += s23 * 136657
        s16 -= s23 * 683901

        s10 += s22 * 666643
        s11 += s22 * 470296
        s12 += s22 * 654183
        s13 -= s22 * 997805
        s14 += s22 * 136657
        s15 -= s22 * 683901

        s9 += s21 * 666643
        s10 += s21 * 470296
        s11 += s21 * 654183
        s12 -= s21 * 997805
        s13 += s21 * 136657
        s14 -= s21 * 683901

        s8 += s20 * 666643
        s9 += s20 * 470296
        s10 += s20 * 654183
        s11 -= s20 * 997805
        s12 += s20 * 136657
        s13 -= s20 * 683901

        s7 += s19 * 666643
        s8 += s19 * 470296
        s9 += s19 * 654183
        s10 -= s19 * 997805
        s11 += s19 * 136657
        s12 -= s19 * 683901

        s6 += s18 * 666643
        s7 += s18 * 470296
        s8 += s18 * 654183
        s9 -= s18 * 997805
        s10 += s18 * 136657
        s11 -= s18 * 683901

        carry6 = (s6 + (1 << 20)) >> 21
        s7 += carry6
        s6 -= carry6 << 21
        carry8 = (s8 + (1 << 20)) >> 21
        s9 += carry8
        s8 -= carry8 << 21
        carry10 = (s10 + (1 << 20)) >> 21
        s11 += carry10
        s10 -= carry10 << 21
        carry12 = (s12 + (1 << 20)) >> 21
        s13 += carry12
        s12 -= carry12 << 21
        carry14 = (s14 + (1 << 20)) >> 21
        s15 += carry14
        s14 -= carry14 << 21
        carry16 = (s16 + (1 << 20)) >> 21
        s17 += carry16
        s16 -= carry16 << 21

        carry7 = (s7 + (1 << 20)) >> 21
        s8 += carry7
        s7 -= carry7 << 21
        carry9 = (s9 + (1 << 20)) >> 21
        s10 += carry9
        s9 -= carry9 << 21
        carry11 = (s11 + (1 << 20)) >> 21
        s12 += carry11
        s11 -= carry11 << 21
        carry13 = (s13 + (1 << 20)) >> 21
        s14 += carry13
        s13 -= carry13 << 21
        carry15 = (s15 + (1 << 20)) >> 21
        s16 += carry15
        s15 -= carry15 << 21

        s5 += s17 * 666643
        s6 += s17 * 470296
        s7 += s17 * 654183
        s8 -= s17 * 997805
        s9 += s17 * 136657
        s10 -= s17 * 683901

        s4 += s16 * 666643
        s5 += s16 * 470296
        s6 += s16 * 654183
        s7 -= s16 * 997805
        s8 += s16 * 136657
        s9 -= s16 * 683901

        s3 += s15 * 666643
        s4 += s15 * 470296
        s5 += s15 * 654183
        s6 -= s15 * 997805
        s7 += s15 * 136657
        s8 -= s15 * 683901

        s2 += s14 * 666643
        s3 += s14 * 470296
        s4 += s14 * 654183
        s5 -= s14 * 997805
        s6 += s14 * 136657
        s7 -= s14 * 683901

        s1 += s13 * 666643
        s2 += s13 * 470296
        s3 += s13 * 654183
        s4 -= s13 * 997805
        s5 += s13 * 136657
        s6 -= s13 * 683901

        s0 += s12 * 666643
        s1 += s12 * 470296
        s2 += s12 * 654183
        s3 -= s12 * 997805
        s4 += s12 * 136657
        s5 -= s12 * 683901
        s12 = 0

        carry0 = (s0 + (1 << 20)) >> 21
        s1 += carry0
        s0 -= carry0 << 21
        carry2 = (s2 + (1 << 20)) >> 21
        s3 += carry2
        s2 -= carry2 << 21
        carry4 = (s4 + (1 << 20)) >> 21
        s5 += carry4
        s4 -= carry4 << 21
        carry6 = (s6 + (1 << 20)) >> 21
        s7 += carry6
        s6 -= carry6 << 21
        carry8 = (s8 + (1 << 20)) >> 21
        s9 += carry8
        s8 -= carry8 << 21
        carry10 = (s10 + (1 << 20)) >> 21
        s11 += carry10
        s10 -= carry10 << 21

        carry1 = (s1 + (1 << 20)) >> 21
        s2 += carry1
        s1 -= carry1 << 21
        carry3 = (s3 + (1 << 20)) >> 21
        s4 += carry3
        s3 -= carry3 << 21
        carry5 = (s5 + (1 << 20)) >> 21
        s6 += carry5
        s5 -= carry5 << 21
        carry7 = (s7 + (1 << 20)) >> 21
        s8 += carry7
        s7 -= carry7 << 21
        carry9 = (s9 + (1 << 20)) >> 21
        s10 += carry9
        s9 -= carry9 << 21
        carry11 = (s11 + (1 << 20)) >> 21
        s12 += carry11
        s11 -= carry11 << 21

        s0 += s12 * 666643
        s1 += s12 * 470296
        s2 += s12 * 654183
        s3 -= s12 * 997805
        s4 += s12 * 136657
        s5 -= s12 * 683901

        carry0 = s0 >> 21
        s1 += carry0
        s0 -= carry0 << 21
        carry1 = s1 >> 21
        s2 += carry1
        s1 -= carry1 << 21
        carry2 = s2 >> 21
        s3 += carry2
        s2 -= carry2 << 21
        carry3 = s3 >> 21
        s4 += carry3
        s3 -= carry3 << 21
        carry4 = s4 >> 21
        s5 += carry4
        s4 -= carry4 << 21
        carry5 = s5 >> 21
        s6 += carry5
        s5 -= carry5 << 21
        carry6 = s6 >> 21
        s7 += carry6
        s6 -= carry6 << 21
        carry7 = s7 >> 21
        s8 += carry7
        s7 -= carry7 << 21
        carry8 = s8 >> 21
        s9 += carry8
        s8 -= carry8 << 21
        carry9 = s9 >> 21
        s10 += carry9
        s9 -= carry9 << 21
        carry10 = s10 >> 21
        s11 += carry10
        s10 -= carry10 << 21

        result = [0] * 32
        result[0] = s0 & 0xFF
        result[1] = (s0 >> 8) & 0xFF
        result[2] = ((s0 >> 16) | (s1 << 5)) & 0xFF
        result[3] = (s1 >> 3) & 0xFF
        result[4] = (s1 >> 11) & 0xFF
        result[5] = ((s1 >> 19) | (s2 << 2)) & 0xFF
        result[6] = (s2 >> 6) & 0xFF
        result[7] = ((s2 >> 14) | (s3 << 7)) & 0xFF
        result[8] = (s3 >> 1) & 0xFF
        result[9] = (s3 >> 9) & 0xFF
        result[10] = ((s3 >> 17) | (s4 << 4)) & 0xFF
        result[11] = (s4 >> 4) & 0xFF
        result[12] = (s4 >> 12) & 0xFF
        result[13] = ((s4 >> 20) | (s5 << 1)) & 0xFF
        result[14] = (s5 >> 7) & 0xFF
        result[15] = ((s5 >> 15) | (s6 << 6)) & 0xFF
        result[16] = (s6 >> 2) & 0xFF
        result[17] = (s6 >> 10) & 0xFF
        result[18] = ((s6 >> 18) | (s7 << 3)) & 0xFF
        result[19] = (s7 >> 5) & 0xFF
        result[20] = (s7 >> 13) & 0xFF
        result[21] = s8 & 0xFF
        result[22] = (s8 >> 8) & 0xFF
        result[23] = ((s8 >> 16) | (s9 << 5)) & 0xFF
        result[24] = (s9 >> 3) & 0xFF
        result[25] = (s9 >> 11) & 0xFF
        result[26] = ((s9 >> 19) | (s10 << 2)) & 0xFF
        result[27] = (s10 >> 6) & 0xFF
        result[28] = ((s10 >> 14) | (s11 << 7)) & 0xFF
        result[29] = (s11 >> 1) & 0xFF
        result[30] = (s11 >> 9) & 0xFF
        result[31] = (s11 >> 17) & 0xFF

        return Ed25519EncodedFieldElement(bytes(result))

    @staticmethod
    def _three_bytes_to_long(data: bytes, offset: int) -> int:
        result = data[offset] & 0xFF
        result |= (data[offset + 1] & 0xFF) << 8
        result |= (data[offset + 2] & 0xFF) << 16
        return c_int64(result).value

    @staticmethod
    def _four_bytes_to_long(data: bytes, offset: int) -> int:
        result = data[offset] & 0xFF
        result |= (data[offset + 1] & 0xFF) << 8
        result |= (data[offset + 2] & 0xFF) << 16
        result |= (data[offset + 3] & 0xFF) << 24
        return c_int64(result).value & 0xFFFFFFFF

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
        if not isinstance(obj, Ed25519EncodedFieldElement):
            return False

        return compare_digest(self.values, obj.values)

    def __str__(self):
        return self.values.hex()
