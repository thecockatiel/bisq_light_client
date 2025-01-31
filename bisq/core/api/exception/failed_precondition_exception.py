from bisq.common.bisq_exception import BisqException


class FailedPreconditionException(BisqException):
    """
    To be thrown in cases when client is attempting to change some state requiring a
    pre-conditional state to exist, e.g., when attempting to lock or unlock a wallet that
    is not encrypted.
    """
    pass
