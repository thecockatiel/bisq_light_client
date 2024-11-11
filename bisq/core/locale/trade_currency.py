from abc import ABC
from functools import total_ordering
import proto.pb_pb2 as protobuf

@total_ordering
class TradeCurrency(ABC):
    code: str
    name: str
    
    def __init__(self, code: str, name: str):
        self.code = code
        self.name = name
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TradeCurrency):
            return False
        return self.code == other.code
    
    def __hash__(self) -> int:
        return hash(self.code)
    
    def __str__(self) -> str:
        return f"TradeCurrency(code={self.code}, name={self.name})"
    
    def __lt__(self, other: 'TradeCurrency') -> bool:
        if not isinstance(other, TradeCurrency):
            return NotImplemented
        return self.name < other.name
    
    @staticmethod
    def from_proto(proto: protobuf.TradeCurrency) -> 'TradeCurrency':
        from bisq.core.locale.fiat_currency import FiatCurrency
        from bisq.core.locale.crypto_currency import CryptoCurrency

        if proto.HasField('fiat_currency'):
            return FiatCurrency.from_proto(proto)
        elif proto.HasField('crypto_currency'):
            return CryptoCurrency.from_proto(proto)
        else:
            raise RuntimeError(f"Unknown message case: {proto.WhichOneof('message')}")
    
    def get_trade_currency_builder(self):
        return protobuf.TradeCurrency(code=self.code, name=self.name)
    
    def get_display_prefix(self) -> str:
        return ""
    
    def get_name_and_code(self) -> str:
        return f"{self.name} ({self.code})"
    
    def get_code_and_name(self) -> str:
        return f"{self.code} ({self.name})"