from typing import Type


class VerificationException(RuntimeError):
    EmptyInputsOrOutputs: Type["EmptyInputsOrOutputs"] = None
    LargerThanMaxBlockSize: Type["LargerThanMaxBlockSize"] = None
    DuplicatedOutPoint: Type["DuplicatedOutPoint"] = None
    NegativeValueOutput: Type["NegativeValueOutput"] = None
    ExcessiveValue: Type["ExcessiveValue"] = None
    CoinbaseScriptSizeOutOfRange: Type["CoinbaseScriptSizeOutOfRange"] = None
    BlockVersionOutOfDate: Type["BlockVersionOutOfDate"] = None
    UnexpectedCoinbaseInput: Type["UnexpectedCoinbaseInput"] = None
    CoinbaseHeightMismatch: Type["CoinbaseHeightMismatch"] = None
    NoncanonicalSignature: Type["NoncanonicalSignature"] = None


class EmptyInputsOrOutputs(VerificationException):
    def __init__(self):
        super().__init__("Transaction had no inputs or no outputs.")


class LargerThanMaxBlockSize(VerificationException):
    def __init__(self):
        super().__init__("Transaction larger than MAX_BLOCK_SIZE")


class DuplicatedOutPoint(VerificationException):
    def __init__(self):
        super().__init__("Duplicated outpoint")


class NegativeValueOutput(VerificationException):
    def __init__(self):
        super().__init__("Transaction output negative")


class ExcessiveValue(VerificationException):
    def __init__(self):
        super().__init__("Total transaction output value greater than possible")


class CoinbaseScriptSizeOutOfRange(VerificationException):
    def __init__(self):
        super().__init__("Coinbase script size out of range")


class BlockVersionOutOfDate(VerificationException):
    def __init__(self, version):
        super().__init__(f"Block version #{version} is outdated.")


class UnexpectedCoinbaseInput(VerificationException):
    def __init__(self):
        super().__init__("Coinbase input as input in non-coinbase transaction")


class CoinbaseHeightMismatch(VerificationException):
    def __init__(self, message):
        super().__init__(message)

class NoncanonicalSignature(VerificationException):
    def __init__(self):
        super().__init__("Signature encoding is not canonical")


VerificationException.EmptyInputsOrOutputs = EmptyInputsOrOutputs
VerificationException.LargerThanMaxBlockSize = LargerThanMaxBlockSize
VerificationException.DuplicatedOutPoint = DuplicatedOutPoint
VerificationException.NegativeValueOutput = NegativeValueOutput
VerificationException.ExcessiveValue = ExcessiveValue
VerificationException.CoinbaseScriptSizeOutOfRange = CoinbaseScriptSizeOutOfRange
VerificationException.BlockVersionOutOfDate = BlockVersionOutOfDate
VerificationException.UnexpectedCoinbaseInput = UnexpectedCoinbaseInput
VerificationException.CoinbaseHeightMismatch = CoinbaseHeightMismatch
VerificationException.NoncanonicalSignature = NoncanonicalSignature
