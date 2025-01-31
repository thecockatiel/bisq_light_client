from typing import TYPE_CHECKING, TypeVar 
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.support.dispute.dispute_list import DisputeList
from bisq.core.support.support_type import SupportType
import pb_pb2 as protobuf
from bisq.core.support.dispute.dispute import Dispute
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver

_T = TypeVar("T", bound="Dispute")

class RefundDisputeList(DisputeList[_T]):
    """
    Holds a List of refund dispute objects.
    
    Calls to the List are delegated because this class intercepts the add/remove calls so changes
    can be saved to disc.
    """
        
    def to_proto_message(self):
        for dispute in self.list:
            check_argument(dispute.support_type == SupportType.REFUND, "Support type has to be REFUND")

        return protobuf.PersistableEnvelope(
            refund_dispute_list=protobuf.RefundDisputeList(
                dispute=ProtoUtil.collection_to_proto(self.list, protobuf.Dispute)
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.RefundDisputeList, core_proto_resolver: "CoreProtoResolver") -> 'RefundDisputeList':
        disputes = [
            Dispute.from_proto(dispute_proto, core_proto_resolver)
            for dispute_proto in proto.dispute
            if Dispute.from_proto(dispute_proto, core_proto_resolver).support_type == SupportType.REFUND
        ]
        return RefundDisputeList(disputes)


