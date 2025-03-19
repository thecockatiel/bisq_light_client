class ByteUtil:

    @staticmethod
    def byte_to_hex(v: int):
        # make sure v is a byte int value
        return hex(v & 0xFF)[2:]

    @staticmethod
    def long_to_little_endian_uint32_byte_array(value: int):
        array = [(value >> (i * 8)) & 0xFF for i in range(4)]
        return bytes(array)

    @staticmethod
    def get_big_integer_from_unsigned_little_endian_byte_array(a1: bytes):
        a = bytearray(a1)
        a.reverse()
        a2 = bytearray(len(a1) + 1)
        a2[1:] = a
        return int.from_bytes(a2, byteorder="big", signed=False)
