from enum import Enum

class TransactionConfidenceType(Enum):
    """Describes the state of the transaction in general terms. Properties can be read to learn specifics."""
    
    BUILDING = 1
    """If BUILDING, then the transaction is included in the best chain and your confidence in it is increasing."""
    
    PENDING = 2
    """If PENDING, then the transaction is unconfirmed and should be included shortly, as long as it is being
    announced and is considered valid by the network. A pending transaction will be announced if the containing
    wallet has been attached to a live PeerGroup. You can estimate how likely the transaction is to be included
    by connecting to nodes then measuring how many announce it. Or if you saw it from a trusted peer,
    you can assume it's valid and will get mined sooner or later as well."""
    
    DEAD = 4
    """If DEAD, then it means the transaction won't confirm unless there is another re-org,
    because some other transaction is spending one of its inputs. Such transactions should be alerted to the user
    so they can take action, eg, suspending shipment of goods if they are a merchant.
    It can also mean that a coinbase transaction has been made dead from it being moved onto a side chain."""
    
    IN_CONFLICT = 5
    """If IN_CONFLICT, then it means there is another transaction (or several other transactions) spending one
    (or several) of its inputs but nor this transaction nor the other/s transaction/s are included in the best chain.
    The other/s transaction/s should be IN_CONFLICT too. IN_CONFLICT can be thought as an intermediary state
    between a) PENDING and BUILDING or b) PENDING and DEAD. Another common name for this situation is "double spend"."""
    
    UNKNOWN = 0
    """If a transaction hasn't been broadcast yet, or there's no record of it, its confidence is UNKNOWN."""
    
    def __init__(self, val: int):
        self.val = val # NOTE: we use val because value is already used by enums in python.

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
