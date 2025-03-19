from typing import Union

from bisq.core.xmr.knaccc.monero.address.byte_util import ByteUtil


class Scalar:

    def __init__(self, bytes_or_hex: Union[bytes, str]):
        if isinstance(bytes_or_hex, bytes):
            self.bytes = bytes_or_hex
        else:
            self.bytes = bytes.fromhex(bytes_or_hex)

    def __str__(self):
        return self.bytes.hex()

    def __eq__(self, other):
        return isinstance(other, Scalar) and self.bytes == other.bytes

    def add(self, a: "Scalar"):
        from bisq.core.xmr.knaccc.monero.crypto.crypto_util import CryptoUtil

        modulus = CryptoUtil.l
        result = (
            ByteUtil.get_big_integer_from_unsigned_little_endian_byte_array(self.bytes)
            + ByteUtil.get_big_integer_from_unsigned_little_endian_byte_array(a.bytes)
        ) % modulus
        return Scalar(
            CryptoUtil.ensure_32_bytes_and_convert_to_little_endian(
                result.to_bytes(32, byteorder="little", signed=False)
            )
        )
