from bisq.common.protocol.persistable.persistable_list import PersistableList
import proto.pb_pb2 as protobuf
from bisq.core.payment.payment_account import PaymentAccount

class PaymentAccountList(PersistableList["PaymentAccount"]):
    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            payment_account_list=protobuf.PaymentAccountList(
                payment_account=[account.to_proto_message() for account in self.list]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountList, core_proto_resolver) -> "PaymentAccountList":
        accounts = [PaymentAccount.from_proto(e, core_proto_resolver) 
                   for e in proto.payment_account]
        accounts = [a for a in accounts if a is not None]
        return PaymentAccountList(accounts)
