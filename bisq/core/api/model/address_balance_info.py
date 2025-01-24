from bisq.common.payload import Payload
import grpc_pb2


class AddressBalanceInfo(Payload):

    def __init__(
        self,
        address: str,
        balance: int,
        num_confirmations: int,
        is_address_unused: bool,
    ):
        self.address = address
        self.balance = balance  # address' balance in satoshis
        self.num_confirmations = (
            num_confirmations  # confirmations for address' most recent tx
        )
        self.is_address_unused = is_address_unused

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return grpc_pb2.AddressBalanceInfo(
            address=self.address,
            balance=self.balance,
            num_confirmations=self.num_confirmations,
            is_address_unused=self.is_address_unused,
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.AddressBalanceInfo):
        return AddressBalanceInfo(
            address=proto.address,
            balance=proto.balance,
            num_confirmations=proto.num_confirmations,
            is_address_unused=proto.is_address_unused,
        )

    def __str__(self):
        return (
            f"AddressBalanceInfo{{address='{self.address}', "
            f"balance={self.balance}, "
            f"num_confirmations={self.num_confirmations}, "
            f"is_address_unused={self.is_address_unused}}}"
        )
