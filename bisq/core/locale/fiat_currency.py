from typing import Union
from bisq.core.locale.global_settings import GlobalSettings
import pb_pb2 as protobuf
from bisq.core.locale.currency_data import CURRENCY_CODE_TO_DATA_MAP, CurrencyData
from bisq.core.locale.trade_currency import TradeCurrency

# TODO: complete ?
class FiatCurrency(TradeCurrency):
    # http://boschista.deviantart.com/journal/Cool-ASCII-Symbols-214218618
    PREFIX = "★ "
    
    currency: CurrencyData

    def __init__(self, code_or_currency_data: Union[str, CurrencyData], locale = None):
        # locale is ignored because we don't support it yet. but we kept it for parity with java bisq
        if isinstance(code_or_currency_data, str):
            self.currency = CURRENCY_CODE_TO_DATA_MAP.get(code_or_currency_data)
        else:
            self.currency = code_or_currency_data
        super().__init__(self.currency.currency_code, self.currency.display_name)

    def get_display_prefix(self):
        return self.PREFIX

    def to_proto_message(self):
        proto_trade_currency = self.get_trade_currency_builder()
        proto_currency = protobuf.Currency(currency_code=self.currency.currency_code)
        proto_fiat_currency = protobuf.FiatCurrency(currency=proto_currency)
        proto_trade_currency.fiat_currency.CopyFrom(proto_fiat_currency)
        return proto_trade_currency

    @staticmethod
    def from_proto(proto: protobuf.TradeCurrency):
        return FiatCurrency(code_or_currency_data=proto.code)

    def get_display_prefix(self):
        return self.PREFIX
    
    @staticmethod
    def get_locale():
        return GlobalSettings.locale_property.get()