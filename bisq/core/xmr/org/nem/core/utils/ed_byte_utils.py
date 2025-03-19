
class EdByteUtils:

    @staticmethod
    def is_equal_constant_time(b: int, c: int) -> int:
        result = 0
        xor = b ^ c
        for i in range(8):
            result |= xor >> i

        return (result ^ 0x01) & 0x01

    @staticmethod
    def is_negative_constant_time(b: int) -> int:
        return (b >> 8) & 1