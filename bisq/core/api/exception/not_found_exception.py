from bisq.common.bisq_exception import BisqException


class NotFoundException(BisqException):
    """
    To be thrown when a file or entity such as an Offer, PaymentAccount, or Trade
    is not found by RPC methods such as GetOffer(id), PaymentAccount(id), or GetTrade(id).
    
    May also be used if a resource such as a File is not found.
    """
    pass
