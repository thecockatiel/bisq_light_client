from abc import ABC
from dataclasses import dataclass, field

from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.extended_data_size_permission import ExtendedDataSizePermission
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
import proto.pb_pb2 as protobuf

@dataclass(kw_only=True)
class FileTransferPart(NetworkEnvelope, ExtendedDataSizePermission, SendersNodeAddressMessage):
    sender_node_address: NodeAddress
    trade_id: str
    trader_id: int
    uid: str
    seq_num_or_file_length: int
    message_data: bytes = field(default=b'') # if message_data is empty it is the first message, requesting file upload permission

    @property
    def is_initial_request(self) -> bool:
        return len(self.message_data) == 0

    @staticmethod
    def from_proto(proto: protobuf.FileTransferPart, message_version: int):
        sender_node_address = NodeAddress.from_proto(proto.sender_node_address)
        trade_id = proto.trade_id
        trader_id = proto.trader_id
        uid = proto.uid
        seq_num_or_file_length = proto.seq_num_or_file_length
        message_data = proto.message_data
        return FileTransferPart(message_version=message_version,
                                sender_node_address=sender_node_address,
                                trade_id=trade_id, 
                                trader_id=trader_id,
                                uid=uid,
                                seq_num_or_file_length=seq_num_or_file_length,
                                message_data=message_data)

    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.file_transfer_part.CopyFrom(protobuf.FileTransferPart(
            senderNodeAddress=self.sender_node_address.to_proto_message(),
            tradeId=self.trade_id,
            traderId=self.trader_id,
            uid=self.uid,
            seqNumOrFileLength=self.seq_num_or_file_length,
            messageData=self.message_data
        ))
        return envelope

    def get_sender_node_address(self) -> NodeAddress:
        return self.sender_node_address

    def __str__(self) -> str:
        return (f"FileTransferPart{{\n"
                f"     senderNodeAddress='{self.sender_node_address.get_host_name_for_display()}',\n"
                f"     uid='{self.uid}',\n"
                f"     tradeId='{self.trade_id}',\n"
                f"     traderId='{self.trader_id}',\n"
                f"     seqNumOrFileLength={self.seq_num_or_file_length}\n"
                f"}} {super().__str__()}")

