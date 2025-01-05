from enum import Enum
from typing import Optional
from utils.hackyway import create_fake_copy_of_instance

# numbers in front of the enum names are ignored, it is set in __new__, it's just for better readability

class XmrTxProofRequestDetail(Enum):
    # Pending
    TX_NOT_FOUND = 0 # Tx not visible in network yet. Could be also other error
    PENDING_CONFIRMATIONS = 1

    SUCCESS = 2

    # Error states
    CONNECTION_FAILURE = 3
    API_INVALID = 4

    # Failure states
    TX_HASH_INVALID = 5
    TX_KEY_INVALID = 6
    ADDRESS_INVALID = 7
    NO_MATCH_FOUND = 8
    AMOUNT_NOT_MATCHING = 9
    TRADE_DATE_NOT_MATCHING = 10
    INVALID_UNLOCK_TIME = 11
    NO_RESULTS_TIMEOUT = 12
    
    def __init__(self, *args):
        super().__init__()
        self.num_confirmations = 0
        self.error_msg: Optional[str] = None

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def with_error(self, error_msg: str) -> 'XmrTxProofRequestDetail':
        return create_fake_copy_of_instance(self, {"error_msg": error_msg})

    def with_num_confirmations(self, num_confirmations: int) -> 'XmrTxProofRequestDetail':
        return create_fake_copy_of_instance(self, {"num_confirmations": num_confirmations})

    def __str__(self) -> str:
        return (f"XmrTxProofRequestDetail {{\n"
                f"     num_confirmations={self.num_confirmations},\n"
                f"     error_msg='{self.error_msg}'\n"
                f"}}")
