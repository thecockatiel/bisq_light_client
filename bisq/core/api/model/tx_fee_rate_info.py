from bisq.common.payload import Payload
import grpc_pb2


class TxFeeRateInfo(Payload):
    def __init__(
        self,
        use_custom_tx_fee_rate: bool,
        custom_tx_fee_rate: int,
        min_fee_service_rate: int,
        fee_service_rate: int,
        last_fee_service_request_ts: int,
    ):
        self.use_custom_tx_fee_rate = use_custom_tx_fee_rate
        self.custom_tx_fee_rate = custom_tx_fee_rate
        self.min_fee_service_rate = min_fee_service_rate
        self.fee_service_rate = fee_service_rate
        self.last_fee_service_request_ts = last_fee_service_request_ts

    # //////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # //////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return grpc_pb2.TxFeeRateInfo(
            use_custom_tx_fee_rate=self.use_custom_tx_fee_rate,
            custom_tx_fee_rate=self.custom_tx_fee_rate,
            fee_service_rate=self.fee_service_rate,
            last_fee_service_request_ts=self.last_fee_service_request_ts,
            min_fee_service_rate=self.min_fee_service_rate,
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.TxFeeRateInfo) -> "TxFeeRateInfo":
        return TxFeeRateInfo(
            use_custom_tx_fee_rate=proto.use_custom_tx_fee_rate,
            custom_tx_fee_rate=proto.custom_tx_fee_rate,
            min_fee_service_rate=proto.min_fee_service_rate,
            fee_service_rate=proto.fee_service_rate,
            last_fee_service_request_ts=proto.last_fee_service_request_ts,
        )

    def __str__(self):
        return (
            "TxFeeRateInfo{\n"
            f"  useCustomTxFeeRate={self.use_custom_tx_fee_rate}\n"
            f", customTxFeeRate={self.custom_tx_fee_rate} sats/byte\n"
            f", minFeeServiceRate={self.min_fee_service_rate} sats/byte\n"
            f", feeServiceRate={self.fee_service_rate} sats/byte\n"
            f", lastFeeServiceRequestTs={self.last_fee_service_request_ts}\n"
            "}"
        )
