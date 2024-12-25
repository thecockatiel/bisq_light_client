from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf

class PriceAlertFilter(PersistablePayload):
    def __init__(self, currency_code: str, high: int, low: int):
        self.currency_code = currency_code
        self.high = high
        self.low = low

    def to_proto_message(self) -> protobuf.PriceAlertFilter:
        return protobuf.PriceAlertFilter(
            currencyCode=self.currency_code, # weird protobuf names
            high=self.high,
            low=self.low
        )

    @staticmethod
    def from_proto(proto: protobuf.PriceAlertFilter) -> 'PriceAlertFilter':
        return PriceAlertFilter(
            currency_code=proto.currencyCode, # weird protobuf names
            high=proto.high,
            low=proto.low
        )

