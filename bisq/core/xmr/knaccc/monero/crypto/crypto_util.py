# TODO: incomplete

class CryptoUtil:
    l = (2 ** 252) + 27742317777372353535851937790883648493
    
    @staticmethod
    def to_canoninal_tx_key(tx_key: str) -> str:
        bytes_ = bytes.fromhex(tx_key)
        as_little_endian_bytes = CryptoUtil.ensure_32_bytes_and_convert_to_little_endian(bytes_)
        result = int.from_bytes(as_little_endian_bytes, byteorder='big') % CryptoUtil.l
        non_malleable = result.to_bytes((result.bit_length() + 7) // 8, byteorder='big')
        non_malleable_as_little_endian = CryptoUtil.ensure_32_bytes_and_convert_to_little_endian(non_malleable)
        return non_malleable_as_little_endian.hex()
        
    @staticmethod
    def ensure_32_bytes_and_convert_to_little_endian(bytes_: bytes) -> bytes:
        s = bytearray(32)
        if len(bytes_) > 32:
            s[:] = bytes_[1:33]
        else:
            s[32 - len(bytes_):] = bytes_
        s.reverse()
        return bytes(s)