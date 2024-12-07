from enum import Enum

from bisq.core.locale.res import Res


class FeeValidationStatus(Enum):
    NOT_CHECKED_YET = "fee.validation.notCheckedYet"
    ACK_FEE_OK = "fee.validation.ack.feeCheckedOk"
    ACK_BSQ_TX_IS_NEW = "fee.validation.ack.bsqTxIsNew"
    ACK_CHECK_BYPASSED = "fee.validation.ack.checkBypassed"
    NACK_BTC_TX_NOT_FOUND = "fee.validation.error.btcTxNotFound"
    NACK_BSQ_FEE_NOT_FOUND = "fee.validation.error.bsqTxNotFound"
    NACK_MAKER_FEE_TOO_LOW = "fee.validation.error.makerFeeTooLow"
    NACK_TAKER_FEE_TOO_LOW = "fee.validation.error.takerFeeTooLow"
    NACK_UNKNOWN_FEE_RECEIVER = "fee.validation.error.unknownReceiver"
    NACK_JSON_ERROR = "fee.validation.error.json"
    
    
    def __init__(self, description_key: str):
        self.description_key = description_key

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    @property
    def passes(self):
        return self in (FeeValidationStatus.ACK_FEE_OK, FeeValidationStatus.ACK_BSQ_TX_IS_NEW, FeeValidationStatus.ACK_CHECK_BYPASSED)
    
    @property
    def fails(self):
        return self != FeeValidationStatus.NOT_CHECKED_YET and not self.passes
    
    def __str__(self):
        try:
            Res.get(self.description_key)
        except:
            return self.description_key
        
