from bitcoinj.wallet.exceptions.completion_exception import CompletionException


class MultipleOpReturnRequested(CompletionException):
    """Thrown if there is more than one OP_RETURN output for the resultant transaction."""
