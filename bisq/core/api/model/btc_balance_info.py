from bisq.common.payload import Payload
import proto.grpc_pb2 as grpc_pb2


class BtcBalanceInfo(Payload):
    EMPTY: "BtcBalanceInfo" = None  # initialized after class creation

    def __init__(
        self,
        available_balance: int,
        reserved_balance: int,
        total_available_balance: int,
        locked_balance: int,
    ):
        # All balances are in BTC satoshis.
        self.available_balance = available_balance
        self.reserved_balance = reserved_balance
        self.total_available_balance = total_available_balance  # available + reserved
        self.locked_balance = locked_balance

    @staticmethod
    def value_of(
        available_balance: int,
        reserved_balance: int,
        total_available_balance: int,
        locked_balance: int,
    ) -> "BtcBalanceInfo":
        # Convenience for creating a model instance instead of a proto.
        return BtcBalanceInfo(
            available_balance,
            reserved_balance,
            total_available_balance,
            locked_balance,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return grpc_pb2.BtcBalanceInfo(
            available_balance=self.available_balance,
            reserved_balance=self.reserved_balance,
            total_available_balance=self.total_available_balance,
            locked_balance=self.locked_balance,
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.BtcBalanceInfo) -> "BtcBalanceInfo":
        return BtcBalanceInfo(
            available_balance=proto.available_balance,
            reserved_balance=proto.reserved_balance,
            total_available_balance=proto.total_available_balance,
            locked_balance=proto.locked_balance,
        )

    def __str__(self):
        return (
            f"BtcBalanceInfo{{available_balance={self.available_balance}, "
            f"reserved_balance={self.reserved_balance}, "
            f"total_available_balance={self.total_available_balance}, "
            f"locked_balance={self.locked_balance}}}"
        )


BtcBalanceInfo.EMPTY = BtcBalanceInfo(-1, -1, -1, -1)
