from bitcoinj.wallet.exceptions.completion_exception import CompletionException


class ExceededMaxTransactionSize(CompletionException):
    """
    Thrown if the resultant transaction is too big for Bitcoin to process. Try breaking up the amounts of value.
    """

    pass
