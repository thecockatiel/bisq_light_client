
def get_var_int_bytes(i: int) -> bytes:
    """Constructs a new VarInt with the given unsigned long value."""
    # Taken from https://github.com/spesmilo/electrum/blob/d2fa65b9aa1d5d8e3b0eadad547935396cb52ea1/electrum/bitcoin.py#L225
    # https://en.bitcoin.it/wiki/Protocol_specification#Variable_length_integer
    # https://github.com/bitcoin/bitcoin/blob/efe1ee0d8d7f82150789f1f6840f139289628a2b/src/serialize.h#L247
    # "CompactSize"
    assert i >= 0, i
    if i < 0xfd:
        return int.to_bytes(i, length=1, byteorder="little", signed=False)
    elif i <= 0xffff:
        return b"\xfd" + int.to_bytes(i, length=2, byteorder="little", signed=False)
    elif i <= 0xffffffff:
        return b"\xfe" + int.to_bytes(i, length=4, byteorder="little", signed=False)
    else:
        return b"\xff" + int.to_bytes(i, length=8, byteorder="little", signed=False)
