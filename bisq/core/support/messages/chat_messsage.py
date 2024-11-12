from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from datetime import timedelta
from typing import ClassVar, List, Optional
from uuid import uuid4
from weakref import ref

from bisq.core.common.user_thread import UserThread
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.attachment import Attachment
from bisq.core.support.dispute.dispute import Dispute
from bisq.core.support.messages.support_message import SupportMessage
from bisq.core.support.support_type import SupportType
from utils.formatting import get_short_id
from utils.time import get_time_ms
import proto.pb_pb2 as protobuf


class ChatMessageListener(ABC):
    @abstractmethod
    def on_message_state_changed(self):
        pass


# TODO: refactor setters

@dataclass(kw_only=True)
class ChatMessage(SupportMessage):
    """
    Message for direct communication between two nodes. Originally built for trader to
    arbitrator communication as no other direct communication was allowed. Arbitrator is
    considered as the server and trader as the client in arbitration chats

    For trader to trader communication the maker is considered to be the server
    and the taker is considered as the client.
    """

    TTL: ClassVar[int] = int(
        timedelta(days=7).total_seconds() * 1000
    )  # 7 days in milliseconds

    uid: str = field(default_factory=lambda: str(uuid4()))

    trade_id: str
    trader_id: int
    # This is only used for the server client relationship
    # If senderIsTrader == true then the sender is the client
    sender_is_trader: bool
    message: str
    attachments: List[Attachment] = field(default_factory=list)
    sender_node_address: NodeAddress
    date: float = field(default_factory=get_time_ms)

    is_system_message: bool = field(default=False)

    # Added in v1.1.6. for trader chat to store if message was shown in popup
    was_displayed: bool = field(default=False)

    # todo move to base class (??? present on original bisq code)
    arrived: bool = field(default=False)
    stored_in_mailbox: bool = field(default=False)
    acknowledged: bool = field(default=False)
    send_message_error: Optional[str] = field(default=None)
    ack_error: Optional[str] = field(default=None)

    _listener: Optional[ref[ChatMessageListener]] = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        self.notify_change_listener()

    # We cannot rename protobuf definition because it would break backward compatibility (???)
    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        message = protobuf.ChatMessage(
            type=SupportType.to_proto_message(self.support_type),
            trade_id=self.trade_id,
            trader_id=self.trader_id,
            sender_is_trader=self.sender_is_trader,
            message=self.message,
            attachments=[
                attachment.to_proto_message() for attachment in self.attachments
            ],
            sender_node_address=self.sender_node_address.to_proto_message(),
            date=self.date,
            arrived=self.arrived,
            stored_in_mailbox=self.stored_in_mailbox,
            is_system_message=self.is_system_message,
            uid=self.uid,
            acknowledged=self.acknowledged,
            was_displayed=self.was_displayed,
            send_message_error=(
                self.send_message_error if self.send_message_error else None
            ),
            ack_error=self.ack_error if self.ack_error else None,
        )
        envelope = self.get_network_envelope_builder()
        envelope.chat_message.CopyFrom(message)
        return envelope

    # The protobuf definition ChatMessage cannot be changed as it would break backward compatibility.
    @staticmethod
    def from_proto(proto: protobuf.ChatMessage, message_version: int) -> "ChatMessage":
        # If we get a msg from an old client type will be ordinal 0 which is the dispute entry and as we only added
        # the trade case it is the desired behaviour.
        return ChatMessage(
            support_type=SupportType.from_proto(proto.type),
            trade_id=proto.trade_id,
            trader_id=proto.trader_id,
            sender_is_trader=proto.sender_is_trader,
            message=proto.message,
            attachments=[
                Attachment.from_proto(attachment) for attachment in proto.attachments
            ],
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            date=proto.date,
            arrived=proto.arrived,
            stored_in_mailbox=proto.stored_in_mailbox,
            uid=proto.uid,
            message_version=message_version,
            acknowledged=proto.acknowledged,
            send_message_error=(
                proto.send_message_error if proto.send_message_error else None
            ),
            ack_error=proto.ack_error if proto.ack_error else None,
            is_system_message=proto.is_system_message,
            was_displayed=proto.was_displayed,
        )

    @staticmethod
    def from_payload_proto(proto: protobuf.ChatMessage) -> "ChatMessage":
        # We have the case that an envelope got wrapped into a payload.
        # We don't check the message version here as it was checked in the carrier envelope already (in connection class)
        # Payloads don't have a message version and are also used for persistence
        # We set the value to -1 to indicate it is set but irrelevant
        return ChatMessage.from_proto(proto, -1)

    def add_all_attachments(self, attachments: List[Attachment]):
        self.attachments.extend(attachments)

    def set_arrived(self, arrived: bool):
        self.arrived = arrived
        self.notify_change_listener()

    def set_stored_in_mailbox(self, stored: bool):
        self.stored_in_mailbox = stored
        self.notify_change_listener()

    def set_acknowledged(self, acknowledged: bool):
        self.acknowledged = acknowledged
        self.notify_change_listener()

    def _ack_timed_out(self):
        if not self.acknowledged and not self.stored_in_mailbox:
            self.set_arrived(False)
            self.set_ack_error("support.errorTimeout")

    def start_ack_timer(self):
        # each chat message notifies the user if an ACK is not received in time
        UserThread.run_after(self._ack_timed_out, timedelta(seconds=60))

    def set_send_message_error(self, error: str):
        self.send_message_error = error
        self.notify_change_listener()

    def set_ack_error(self, error: str):
        self.ack_error = error
        self.notify_change_listener()

    def get_trade_id(self) -> str:
        return self.trade_id

    def get_short_id(self) -> str:
        return get_short_id(self.trade_id)

    def add_weak_message_state_listener(self, listener):
        self._listener = ref(listener)

    def is_result_message(self, dispute: "Dispute") -> bool:
        dispute_result = dispute.dispute_result
        if dispute_result is None:
            return False
        result_chat_message = dispute_result.chat_message
        return result_chat_message is not None and result_chat_message.uid == self.uid

    def get_ttl(self) -> int:
        return self.TTL

    def notify_change_listener(self):
        if self._listener is not None:
            listener = self._listener()
            if listener is not None:
                listener.on_message_state_changed()

    def __str__(self):
        return (
            f"ChatMessage{{\n"
            f"     trade_id='{self.trade_id}',\n"
            f"     trader_id={self.trader_id},\n"
            f"     sender_is_trader={self.sender_is_trader},\n"
            f"     message='{self.message}',\n"
            f"     attachments={self.attachments},\n"
            f"     sender_node_address={self.sender_node_address},\n"
            f"     date={self.date},\n"
            f"     is_system_message={self.is_system_message},\n"
            f"     was_displayed={self.was_displayed},\n"
            f"     arrived={self.arrived},\n"
            f"     stored_in_mailbox={self.stored_in_mailbox},\n"
            f"     acknowledged={self.acknowledged},\n"
            f"     send_message_error={self.send_message_error},\n"
            f"     ack_error={self.ack_error}\n"
            f"}} {super().__str__()}"
        )
