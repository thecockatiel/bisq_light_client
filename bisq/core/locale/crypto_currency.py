import proto.pb_pb2 as protobuf
from bisq.core.locale.trade_currency import TradeCurrency


class CryptoCurrency(TradeCurrency):
    PREFIX = "✦ "

    def __init__(self, currency_code: str, name: str, is_asset: bool = False):
        super().__init__(currency_code, name)
        self._is_asset = is_asset

    @property
    def is_asset(self) -> bool:
        return self._is_asset

    def to_proto_message(self):
        trade_currency = self.get_trade_currency_builder()
        trade_currency.crypto_currency.CopyFrom(
            protobuf.CryptoCurrency(is_asset=self._is_asset)
        )
        return trade_currency

    @staticmethod
    def from_proto(proto: protobuf.TradeCurrency) -> 'CryptoCurrency':
        return CryptoCurrency(
            currency_code=proto.code,
            name=proto.name,
            is_asset=proto.crypto_currency.is_asset
        )

    def get_display_prefix(self) -> str:
        return self.PREFIX

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CryptoCurrency):
            return False
        return (super().__eq__(other) and 
                self._is_asset == other._is_asset)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._is_asset))