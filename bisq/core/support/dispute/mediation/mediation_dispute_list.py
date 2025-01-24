from typing import TYPE_CHECKING, TypeVar 
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.support.dispute.dispute_list import DisputeList
from bisq.core.support.support_type import SupportType
import pb_pb2 as protobuf
from bisq.core.support.dispute.dispute import Dispute

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver

_T = TypeVar("T", bound="Dispute")

class MediationDisputeList(DisputeList[_T]):
    """
    Holds a List of mediation dispute objects.
    
    Calls to the List are delegated because this class intercepts the add/remove calls so changes
    can be saved to disc.
    """
        
    def to_proto_message(self):
        for dispute in self.list:
            assert dispute.support_type == SupportType.MEDIATION, "Support type has to be MEDIATION"

        return protobuf.PersistableEnvelope(
            mediation_dispute_list=protobuf.MediationDisputeList(
                dispute=ProtoUtil.collection_to_proto(self.list, protobuf.Dispute)
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.MediationDisputeList, core_proto_resolver: "CoreProtoResolver") -> 'MediationDisputeList':
        disputes = [
            Dispute.from_proto(dispute_proto, core_proto_resolver)
            for dispute_proto in proto.dispute
            if Dispute.from_proto(dispute_proto, core_proto_resolver).support_type == SupportType.MEDIATION
        ]
        return MediationDisputeList(disputes)


