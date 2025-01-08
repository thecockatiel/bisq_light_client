from typing import Type


class VerificationException(RuntimeError):
    EMPTY_INPUTS_OR_OUTPUTS: Type["EmptyInputsOrOutputs"] = None
    LARGER_THAN_MAX_BLOCK_SIZE: Type["LargerThanMaxBlockSize"] = None
    DUPLICATED_OUTPOINT: Type["DuplicatedOutPoint"] = None
    NEGATIVE_VALUE_OUTPUT: Type["NegativeValueOutput"] = None
    EXCESSIVE_VALUE: Type["ExcessiveValue"] = None
    COINBASE_SCRIPT_SIZE_OUT_OF_RANGE: Type["CoinbaseScriptSizeOutOfRange"] = None
    BLOCK_VERSION_OUT_OF_DATE: Type["BlockVersionOutOfDate"] = None
    UNEXPECTED_COINBASE_INPUT: Type["UnexpectedCoinbaseInput"] = None
    COINBASE_HEIGHT_MISMATCH: Type["CoinbaseHeightMismatch"] = None


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


VerificationException.EMPTY_INPUTS_OR_OUTPUTS = EmptyInputsOrOutputs
VerificationException.LARGER_THAN_MAX_BLOCK_SIZE = LargerThanMaxBlockSize
VerificationException.DUPLICATED_OUTPOINT = DuplicatedOutPoint
VerificationException.NEGATIVE_VALUE_OUTPUT = NegativeValueOutput
VerificationException.EXCESSIVE_VALUE = ExcessiveValue
VerificationException.COINBASE_SCRIPT_SIZE_OUT_OF_RANGE = CoinbaseScriptSizeOutOfRange
VerificationException.BLOCK_VERSION_OUT_OF_DATE = BlockVersionOutOfDate
VerificationException.UNEXPECTED_COINBASE_INPUT = UnexpectedCoinbaseInput
VerificationException.COINBASE_HEIGHT_MISMATCH = CoinbaseHeightMismatch
