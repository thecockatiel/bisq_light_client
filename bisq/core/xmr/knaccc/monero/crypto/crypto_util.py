# TODO: incomplete

from bisq.common.crypto.hash import get_keccak1600_hash
from bisq.core.xmr.knaccc.monero.address.byte_util import ByteUtil
from bisq.core.xmr.knaccc.monero.crypto.scalar import Scalar


class CryptoUtil:

    @staticmethod
    def hash_to_scalar(a: bytes) -> Scalar:
        hashed = get_keccak1600_hash(a)
        reduced = CryptoUtil.sc_reduce32(hashed)
        return Scalar(reduced)

    l = (2**252) + 27742317777372353535851937790883648493

    @staticmethod
    def to_canoninal_tx_key(tx_key: str) -> str:
        bytes_ = bytes.fromhex(tx_key)
        as_little_endian_bytes = (
            CryptoUtil.ensure_32_bytes_and_convert_to_little_endian(bytes_)
        )
        result = int.from_bytes(as_little_endian_bytes, byteorder="big") % CryptoUtil.l
        non_malleable = result.to_bytes((result.bit_length() + 7) // 8, byteorder="big")
        non_malleable_as_little_endian = (
            CryptoUtil.ensure_32_bytes_and_convert_to_little_endian(non_malleable)
        )
        return non_malleable_as_little_endian.hex()

    @staticmethod
    def sc_reduce32(a: bytes) -> bytes:
        result = (
            ByteUtil.get_big_integer_from_unsigned_little_endian_byte_array(a)
            % CryptoUtil.l
        )
        reduced = result.to_bytes((result.bit_length() + 7) // 8, byteorder="big")
        return CryptoUtil.ensure_32_bytes_and_convert_to_little_endian(reduced)

    @staticmethod
    def ensure_32_bytes_and_convert_to_little_endian(bytes_: bytes) -> bytes:
        s = bytearray(32)
        if len(bytes_) > 32:
            s[:] = bytes_[1:33]
        else:
            s[32 - len(bytes_) :] = bytes_
        s.reverse()
        return bytes(s)
