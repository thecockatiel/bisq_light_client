from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf

class PriceAlertFilter(PersistablePayload):
    def __init__(self, currency_code: str, high: int, low: int):
        self.currency_code = currency_code
        self.high = high
        self.low = low

    def to_proto_message(self) -> protobuf.PriceAlertFilter:
        return protobuf.PriceAlertFilter(
            currency_code=self.currency_code,
            high=self.high,
            low=self.low
        )

    @staticmethod
    def from_proto(proto: protobuf.PriceAlertFilter) -> 'PriceAlertFilter':
        return PriceAlertFilter(
            currency_code=proto.currencyCode,
            high=proto.high,
            low=proto.low
        )

