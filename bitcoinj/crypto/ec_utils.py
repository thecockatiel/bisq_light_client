
def is_compressed_pubkey(ec_pubkey: bytes) -> bool:
    """
    Returns whether the given public key is compressed.
    """
    if ec_pubkey and (ec_pubkey[0] == 0x02 or ec_pubkey[0] == 0x03):
        return True
    return False
