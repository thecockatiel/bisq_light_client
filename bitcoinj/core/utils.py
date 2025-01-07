
import hashlib


def encode_mpi(value: int, include_length: bool) -> bytes:
    """
    MPI encoded numbers are produced by the OpenSSL BN_bn2mpi function. They consist of
    a 4 byte big endian length field, followed by the stated number of bytes representing
    the number in big endian format (with a sign bit).
    Args:
        value (int): The integer value to encode.
        include_length (bool): Indicates whether the 4 byte length field should be included.
    Returns:
        bytes: The MPI encoded byte representation of the integer.
    """
    if value == 0:
        if not include_length:
            return b''
        else:
            return b'\x00\x00\x00\x00'
    
    is_negative = value < 0
    if is_negative:
        value = -value
    
    array = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big')
    length = len(array)
    
    if array[0] & 0x80 == 0x80:
        length += 1
    
    if include_length:
        result = bytearray(length + 4)
        result[0:4] = length.to_bytes(4, byteorder='big')
        result[4 + length - len(array):] = array
        if is_negative:
            result[4] |= 0x80
        return bytes(result)
    else:
        if length != len(array):
            result = bytearray(length)
            result[1:] = array
        else:
            result = bytearray(array)
        if is_negative:
            result[0] |= 0x80
        return bytes(result)
    
def decode_mpi(mpi: bytes, has_length: bool) -> int:
    """
    MPI encoded numbers are produced by the OpenSSL BN_bn2mpi function. They consist of
    a 4 byte big endian length field, followed by the stated number of bytes representing
    the number in big endian format (with a sign bit).
    Args:
        mpi (bytes): The MPI encoded number.
        has_length (bool): Indicates if the given array includes the 4 byte length field.
                           Set to False if the array is missing the length field.
    Returns:
        int: The decoded integer.
    """
    if has_length:
        length = int.from_bytes(mpi[:4], byteorder='big')
        buf = mpi[4:4 + length]
    else:
        buf = mpi
    
    if len(buf) == 0:
        return 0
    
    is_negative = (buf[0] & 0x80) == 0x80
    if is_negative:
        buf = bytearray(buf)
        buf[0] &= 0x7F
    
    result = int.from_bytes(buf, byteorder='big')
    return -result if is_negative else result

def sha1(data: bytes) -> bytes:
    return hashlib.sha1(data).digest()
