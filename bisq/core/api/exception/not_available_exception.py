from bisq.common.bisq_exception import BisqException


class NotAvailableException(BisqException):
    """
    To be thrown in cases where some service or value, e.g.,
    a wallet balance, or sufficient funds are unavailable.
    """
    pass
