from typing import List, Optional
from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.setup.log_setup import get_logger
import proto.pb_pb2 as protobuf
from bisq.core.network.p2p.mailbox.mailbox_item import MailboxItem

logger = get_logger(__name__)

class MailboxMessageList(PersistableList[MailboxItem]):
    def __init__(self, items: Optional[List[MailboxItem]] = None):
        super().__init__(items)

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            mailbox_message_list=protobuf.MailboxMessageList(
                mailbox_item=[item.to_proto_message() for item in self.list]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.MailboxMessageList, network_proto_resolver: "NetworkProtoResolver"):
        items = []
        for item_proto in proto.mailbox_item:
            try:
                mailbox_item = MailboxItem.from_proto(item_proto, network_proto_resolver)
                if mailbox_item is not None:
                    items.append(mailbox_item)
            except ProtobufferException as e:
                logger.error(f"Error at MailboxItem.from_proto: {str(e)}", exc_info=e)
                
        return MailboxMessageList(items)
