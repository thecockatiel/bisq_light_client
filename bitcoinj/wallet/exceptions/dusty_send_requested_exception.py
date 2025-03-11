from bitcoinj.wallet.exceptions.completion_exception import CompletionException


class DustySendRequestedException(CompletionException):
    """Thrown if the resultant transaction would violate the dust rules (an output that's too small to be worthwhile)."""
    pass
