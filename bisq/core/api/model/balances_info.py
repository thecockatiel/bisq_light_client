from bisq.common.payload import Payload
from bisq.core.api.model.bsq_balance_info import BsqBalanceInfo
from bisq.core.api.model.btc_balance_info import BtcBalanceInfo
import proto.grpc_pb2 as grpc_pb2


class BalancesInfo(Payload):
    def __init__(self, bsq: "BsqBalanceInfo", btc: "BtcBalanceInfo"):
        self.bsq = bsq
        self.btc = btc

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> grpc_pb2.BalancesInfo:
        return grpc_pb2.BalancesInfo(
            bsq=self.bsq.to_proto_message(),
            btc=self.btc.to_proto_message(),
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.BalancesInfo) -> "BalancesInfo":
        return BalancesInfo(
            bsq=BsqBalanceInfo.from_proto(proto.bsq),
            btc=BtcBalanceInfo.from_proto(proto.btc),
        )

    def __str__(self) -> str:
        return (
            #
            "BalancesInfo{\n"
            f"  {self.bsq},\n"
            f"  {self.btc}\n"
            "}"
        )
