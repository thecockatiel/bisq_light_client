from bisq.common.crypto.hash import get_keccak1600_hash


class CryptoNoteException(Exception):
    def __init__(self, msg_or_exception):
        super().__init__(msg_or_exception)
        
class MoneroBase58():
    ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    ALPHABET_SIZE = len(ALPHABET)
    FULL_DECODED_BLOCK_SIZE = 8
    FULL_ENCODED_BLOCK_SIZE = 11
    UINT64_MAX = 18446744073709551615
    DECODED_CHUNK_LENGTH = {
        2: 1,
        3: 2,
        5: 3,
        6: 4,
        7: 5,
        9: 6,
        10: 7,
        11: 8,
    }
    
    @staticmethod
    def decode_chunk(input_str: str,
                 input_offset: int,
                 input_length: int,
                 decoded: bytearray,
                 decoded_offset: int,
                 decoded_length: int) -> None:
        result = 0
        order = 1
        
        # Process input from right to left
        for i in range(input_offset + input_length - 1, input_offset - 1, -1):
            character = input_str[i]
            digit = MoneroBase58.ALPHABET.find(character)
            
            if digit == -1:
                raise CryptoNoteException(f"invalid character {character}")
                
            result += order * digit
            if result > MoneroBase58.UINT64_MAX:
                raise CryptoNoteException(f"64-bit unsigned integer overflow {result}")
                
            order *= MoneroBase58.ALPHABET_SIZE
            
        # Check for capacity overflow
        max_capacity = 1 << (8 * decoded_length)
        if result >= max_capacity:
            raise CryptoNoteException(f"capacity overflow {result}")
            
        # Write bytes from right to left
        for i in range(decoded_offset + decoded_length - 1, decoded_offset - 1, -1):
            decoded[i] = result & 0xFF
            result >>= 8
    
    @staticmethod
    def decode(input_str: str) -> bytes:
        if not input_str:
            return bytes()

        # Calculate sizes
        chunks = len(input_str) // MoneroBase58.FULL_ENCODED_BLOCK_SIZE
        last_encoded_size = len(input_str) % MoneroBase58.FULL_ENCODED_BLOCK_SIZE
        last_chunk_size = MoneroBase58.DECODED_CHUNK_LENGTH.get(last_encoded_size, 0) if last_encoded_size > 0 else 0

        # Create result buffer
        result = bytearray(chunks * MoneroBase58.FULL_DECODED_BLOCK_SIZE + last_chunk_size)
        input_offset = 0
        result_offset = 0

        # Process full chunks
        for chunk in range(chunks):
            MoneroBase58.decode_chunk(
                input_str,
                input_offset,
                MoneroBase58.FULL_ENCODED_BLOCK_SIZE,
                result,
                result_offset,
                MoneroBase58.FULL_DECODED_BLOCK_SIZE
            )
            input_offset += MoneroBase58.FULL_ENCODED_BLOCK_SIZE
            result_offset += MoneroBase58.FULL_DECODED_BLOCK_SIZE

        # Process last partial chunk if exists
        if last_chunk_size > 0:
            MoneroBase58.decode_chunk(
                input_str,
                input_offset,
                last_encoded_size,
                result,
                result_offset,
                last_chunk_size
            )

        return bytes(result)
    
    @staticmethod
    def read_var_int(buffer: bytes, offset: int = 0) -> tuple[int, int]:
        result = 0
        shift = 0
        current_offset = offset
        
        while True:
            current = buffer[current_offset]
            result += (current & 0x7f) << shift
            current_offset += 1
            if (current & 0x80) == 0:
                break
            shift += 7
        
        return result, current_offset - offset

    @staticmethod
    def decode_address(address: str, validate_checksum: bool = False) -> int:
        decoded = MoneroBase58.decode(address)
        
        checksum_size = 4
        if len(decoded) < checksum_size:
            raise CryptoNoteException("invalid length")
        
        decoded_address = decoded[:-checksum_size]
        
        # Read the prefix (variable length integer)
        prefix, _ = MoneroBase58.read_var_int(decoded_address)
        
        if not validate_checksum:
            return prefix
        
        # Validate checksum
        fast_hash = get_keccak1600_hash(decoded_address)
        checksum = int.from_bytes(fast_hash[:4], byteorder='little')
        expected = int.from_bytes(decoded[-checksum_size:], byteorder='little')
        
        if checksum != expected:
            raise CryptoNoteException(
                f"invalid checksum {checksum:08X}, expected {expected:08X}"
            )
        
        return prefix
