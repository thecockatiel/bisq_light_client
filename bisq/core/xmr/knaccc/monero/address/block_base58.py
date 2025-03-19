class BlockBase58:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    encoded_block_sizes = (0, 2, 3, 5, 6, 7, 9, 10, 11)
    full_block_size = 8
    full_encoded_block_size = 11
    UINT64_MAX = 1 << 64

    @staticmethod
    def lookup_index(array, match):
        index = -1
        for i, value in enumerate(array):
            if value == match:
                index = i
        return index

    @staticmethod
    def decode_block(data: str, buf: bytearray, index: int) -> bytearray:
        if len(data) < 1 or len(data) > BlockBase58.full_encoded_block_size:
            raise ValueError(f"Invalid block length: {len(data)}")

        res_size = BlockBase58.lookup_index(BlockBase58.encoded_block_sizes, len(data))
        if res_size <= 0:
            raise ValueError("Invalid block size")

        res_num = 0
        order = 1
        for char in reversed(data):
            digit = BlockBase58.alphabet.find(char)
            if digit < 0:
                raise ValueError("Invalid symbol")
            product = order * digit + res_num
            if product >= BlockBase58.UINT64_MAX:
                raise ValueError("Overflow")
            res_num = product
            order *= len(BlockBase58.alphabet)

        if res_size < BlockBase58.full_block_size and (1 << (8 * res_size)) <= res_num:
            raise ValueError("Overflow 2")

        a = BlockBase58.uint64_to_8be(res_num, res_size)
        buf[index : index + len(a)] = a
        return buf

    @staticmethod
    def uint64_to_8be(n: int, size: int) -> bytes:
        r = bytearray(size)
        a = n.to_bytes((n.bit_length() + 7) // 8, byteorder="big")
        if len(a) <= len(r):
            r[-len(a) :] = a
        else:
            r = a[-len(r) :]
        return r

    @staticmethod
    def decode(data: str) -> bytes:
        full_block_count = len(data) // BlockBase58.full_encoded_block_size
        last_block_size = len(data) % BlockBase58.full_encoded_block_size
        last_block_decoded_size = BlockBase58.lookup_index(
            BlockBase58.encoded_block_sizes, last_block_size
        )
        if last_block_decoded_size < 0:
            raise ValueError("Invalid encoded length")

        data_size = (
            full_block_count * BlockBase58.full_block_size + last_block_decoded_size
        )
        buf = bytearray(data_size)
        for i in range(full_block_count):
            BlockBase58.decode_block(
                data[
                    i
                    * BlockBase58.full_encoded_block_size : (i + 1)
                    * BlockBase58.full_encoded_block_size
                ],
                buf,
                i * BlockBase58.full_block_size,
            )
        if last_block_size > 0:
            BlockBase58.decode_block(
                data[
                    full_block_count
                    * BlockBase58.full_encoded_block_size : full_block_count
                    * BlockBase58.full_encoded_block_size
                    + last_block_size
                ],
                buf,
                full_block_count * BlockBase58.full_block_size,
            )
        return bytes(buf)

    @staticmethod
    def encode_block(data: bytes, buf: list, index: int):
        if len(data) < 1 or len(data) > BlockBase58.full_encoded_block_size:
            raise ValueError(f"Invalid block length: {len(data)}")

        data_zero_padded = bytearray(len(data) + 1)
        data_zero_padded[1:] = data

        num = int.from_bytes(data_zero_padded, byteorder="big")
        i = BlockBase58.encoded_block_sizes[len(data)] - 1
        while num > 0:
            num, remainder = divmod(num, len(BlockBase58.alphabet))
            buf[index + i] = BlockBase58.alphabet[remainder]
            i -= 1

    @staticmethod
    def encode(data: bytes) -> str:
        full_block_count = len(data) // BlockBase58.full_block_size
        last_block_size = len(data) % BlockBase58.full_block_size
        res_size = (
            full_block_count * BlockBase58.full_encoded_block_size
            + BlockBase58.encoded_block_sizes[last_block_size]
        )

        res = [""] * res_size
        for i in range(res_size):
            res[i] = BlockBase58.alphabet[0]
        for i in range(full_block_count):
            BlockBase58.encode_block(
                BlockBase58._subarray(
                    data,
                    i * BlockBase58.full_block_size,
                    i * BlockBase58.full_block_size + BlockBase58.full_block_size,
                ),
                res,
                i * BlockBase58.full_encoded_block_size,
            )
        if last_block_size > 0:
            BlockBase58.encode_block(
                BlockBase58._subarray(
                    data,
                    full_block_count * BlockBase58.full_block_size,
                    full_block_count * BlockBase58.full_block_size + last_block_size,
                ),
                res,
                full_block_count * BlockBase58.full_encoded_block_size,
            )
        return "".join(res)

    @staticmethod
    def _subarray(array: bytes, start: int, end: int) -> bytes:
        return array[start:end]
