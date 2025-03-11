from bitcoinj.wallet.exceptions.completion_exception import CompletionException


class CouldNotAdjustDownwards(CompletionException):
    """
    Thrown when we were trying to empty the wallet, and the total amount of money we were trying to empty after being reduced
    for the fee was smaller than the min payment. Note that the missing field will be null in this case.
    """

    pass
