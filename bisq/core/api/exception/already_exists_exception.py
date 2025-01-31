from bisq.common.bisq_exception import BisqException


class AlreadyExistsException(BisqException):
    """
    To be thrown in cases when some value or state already exists, e.g., trying to lock
    an encrypted wallet that is already locked.
    """
    pass
