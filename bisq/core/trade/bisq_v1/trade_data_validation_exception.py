
class TradeDataValidationException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        
class TradeDataMissingTxException(TradeDataValidationException):
    pass

class TradeDataInvalidTxException(TradeDataValidationException):
    pass

class TradeDataInvalidAmountException(TradeDataValidationException):
    pass

class TradeDataInvalidLockTimeException(TradeDataValidationException):
    pass

class TradeDataInvalidInputException(TradeDataValidationException):
    pass
