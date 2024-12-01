from typing import TYPE_CHECKING, TypeVar 
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.support.dispute.dispute_list import DisputeList
from bisq.core.support.support_type import SupportType
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
    from bisq.core.support.dispute.dispute import Dispute

_T = TypeVar("T", bound="Dispute")

class ArbitrationDisputeList(DisputeList[_T]):
    """
    Holds a List of arbitration dispute objects.
    
    Calls to the List are delegated because this class intercepts the add/remove calls so changes
    can be saved to disc.
    """
        
    def to_proto_message(self):
        for dispute in self.list:
            assert dispute.support_type == SupportType.ARBITRATION, "Support type has to be ARBITRATION"

        return protobuf.PersistableEnvelope(
            arbitration_dispute_list=protobuf.ArbitrationDisputeList(
                dispute=ProtoUtil.collection_to_proto(self.list, protobuf.Dispute)
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.ArbitrationDisputeList, core_proto_resolver: "CoreProtoResolver") -> 'ArbitrationDisputeList':
        disputes = [
            Dispute.from_proto(dispute_proto, core_proto_resolver)
            for dispute_proto in proto.dispute
            if Dispute.from_proto(dispute_proto, core_proto_resolver).support_type == SupportType.ARBITRATION
        ]
        return ArbitrationDisputeList(disputes)


