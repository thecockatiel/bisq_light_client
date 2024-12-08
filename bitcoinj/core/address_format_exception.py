class AddressFormatException(ValueError):
    def __init__(self, message=None):
        super().__init__(message)


class InvalidCharacter(AddressFormatException):
        """
        This exception is thrown by Base58, Bech32 and the PrefixedChecksummedBytes hierarchy of
        classes when you try to decode data and a character isn't valid. You shouldn't allow the user to proceed in this
        case.
        """
        def __init__(self, character: str, position: int):
            self.character = character
            self.position = position
            super().__init__(f"Invalid character '{character}' at position {position}")

class InvalidDataLength(AddressFormatException):
    """
    This exception is thrown by Base58, Bech32 and the PrefixedChecksummedBytes hierarchy of
    classes when you try to decode data and the data isn't of the right size. You shouldn't allow the user to proceed
    in this case.
    """
    def __init__(self, message=None):
        super().__init__(message)

class InvalidChecksum(AddressFormatException):
    """
    This exception is thrown by Base58, Bech32 and the PrefixedChecksummedBytes hierarchy of
    classes when you try to decode data and the checksum isn't valid. You shouldn't allow the user to proceed in this
    case.
    """
    def __init__(self, message=None):
        super().__init__(message if message else "Checksum does not validate")

class InvalidPrefix(AddressFormatException):
    """
    This exception is thrown by the PrefixedChecksummedBytes hierarchy of classes when you try and decode an
    address or private key with an invalid prefix (version header or human-readable part). You shouldn't allow the
    user to proceed in this case.
    """
    def __init__(self, message=None):
        super().__init__(message)

class WrongNetwork(InvalidPrefix):
    """
    This exception is thrown by the PrefixedChecksummedBytes hierarchy of classes when you try and decode an
    address with a prefix (version header or human-readable part) that used by another network (usually: mainnet vs
    testnet). You shouldn't allow the user to proceed in this case as they are trying to send money across different
    chains, an operation that is guaranteed to destroy the money.
    """
    def __init__(self, version_header: int=None, hrp: str=None):
        if version_header is not None:
            message = f"Version code of address did not match acceptable versions for network: {version_header}"
        elif hrp is not None:
            message = f"Human readable part of address did not match acceptable HRPs for network: {hrp}"
        else:
            message = "WrongNetwork"
        super().__init__(message)
