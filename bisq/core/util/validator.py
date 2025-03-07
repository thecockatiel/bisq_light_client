from bisq.core.trade.protocol.trade_message import TradeMessage
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument

class Validator:
    """Utility class for validating domain data."""
    
    @staticmethod
    def non_empty_string_of(value: str) -> str:
        assert value is not None, "Value must not be None"
        check_argument(len(value) > 0, "String must not be empty")
        return value
    
    @staticmethod
    def non_negative_long_of(value: int) -> int:
        check_argument(value >= 0, "Value must be non-negative")
        return value
    
    @staticmethod
    def non_zero_coin_of(value: Coin) -> Coin:
        assert value is not None, "Coin must not be None"
        check_argument(not value.is_zero(), "Coin must not be zero")
        return value
    
    @staticmethod
    def positive_coin_of(value: Coin) -> Coin:
        assert value is not None, "Coin must be None"
        check_argument(value.is_positive(), "Coin must be positive")
        return value
    
    @staticmethod
    def check_trade_id(trade_id: str, trade_message: TradeMessage) -> None:
        check_argument(Validator.is_trade_id_valid(trade_id, trade_message), "Invalid trade ID")
    
    @staticmethod
    def is_trade_id_valid(trade_id: str, trade_message: TradeMessage) -> bool:
        return trade_id == trade_message.trade_id


