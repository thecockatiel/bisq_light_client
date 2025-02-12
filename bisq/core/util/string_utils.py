def string_difference(str1: str, str2: str) -> str:
    """
    Find the difference between two strings, similar to Apache StringUtils.difference()
    Returns the portion of str2 that differs from str1

    Args:
        str1: First string to compare
        str2: Second string to compare
    Returns:
        The portion of str2 that differs from str1
    """
    if str1 is None:
        str1 = ""
    if str2 is None:
        str2 = ""

    # Find index where strings start to differ
    min_length = min(len(str1), len(str2))
    index = 0

    while index < min_length and str1[index] == str2[index]:
        index += 1

    return str2[index:]


def hex_decode_last_4_bytes(hex_string: str) -> bytes:
    return bytes.fromhex(hex_string[-8:])
