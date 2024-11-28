from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import uuid4
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.locale.res import Res
from bisq.core.support.support_type import SupportType
from bisq.core.trade.model.bisq_v1.contract import Contract
from bisq.common.setup.log_setup import get_logger
import proto.pb_pb2 as protobuf
from utils.formatting import get_short_id

logger = get_logger(__name__)

if TYPE_CHECKING:
    from bisq.core.support.messages.chat_messsage import ChatMessage
    from bisq.core.support.dispute.dispute_result import DisputeResult
    from bisq.core.support.dispute.mediation.file_transfer_session import (
        FileTransferSession,
    )
    from bisq.core.support.dispute.mediation.file_transfer_receiver import (
        FileTransferReceiver,
    )
    from bisq.core.support.dispute.mediation.file_transfer_sender import (
        FileTransferSender,
    )
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver


class DisputeState(IntEnum):
    NEEDS_UPGRADE = 0
    NEW = 1
    OPEN = 2
    REOPENED = 3
    CLOSED = 4
    RESULT_PROPOSED = 5

    @staticmethod
    def from_proto(state: protobuf.Dispute.State) -> "DisputeState":
        return ProtoUtil.enum_from_proto(DisputeState, protobuf.Dispute.State, state)

    @staticmethod
    def to_proto_message(state: "DisputeState") -> protobuf.Dispute.State:
        return ProtoUtil.proto_enum_from_enum(protobuf.Dispute.State, state)


@dataclass(kw_only=True)
class Dispute(NetworkPayload, PersistablePayload):
    trade_id: str
    id: str
    trader_id: int
    dispute_opener_is_buyer: bool
    dispute_opener_is_maker: bool
    # PubKeyRing of trader who opened the dispute
    trader_pub_key_ring: PubKeyRing
    trade_date: int # ms timestamp
    trade_period_end: int
    contract: Contract
    contract_hash: Optional[bytes] = field(default=None)
    deposit_tx_serialized: Optional[bytes] = field(default=None)
    payout_tx_serialized: Optional[bytes] = field(default=None)
    deposit_tx_id: Optional[str] = field(default=None)
    payout_tx_id: Optional[str] = field(default=None)
    contract_as_json: str
    maker_contract_signature: Optional[str] = field(default=None)
    taker_contract_signature: Optional[str] = field(default=None)
    agent_pub_key_ring: PubKeyRing  # dispute agent
    is_support_ticket: bool
    chat_messages: List["ChatMessage"] = field(default_factory=list)
    dispute_result: Optional["DisputeResult"] = field(default=None)
    openning_date: int
    dispute_payout_tx_id: Optional[str] = field(default=None)
    # Added v1.2.0: support type
    support_type: SupportType
    # Only used at refundAgent so that he knows how the mediator resolved the case:
    mediators_dispute_result: Optional[str] = field(default=None)
    delayed_payout_tx_id: Optional[str] = field(default=None)

    # Added at v1.4.0
    donation_address_of_delayed_payout_tx: Optional[str] = field(default=None)

    # Added at v1.6.0
    dispute_state: DisputeState = field(default=DisputeState.NEW)

    # Added in v 1.9.7
    burning_man_selection_height: int
    trade_tx_fee: int

    # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
    # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
    # field in a class would break that hash and therefore break the storage mechanism.
    extra_data_map: Optional[Dict[str, str]] = field(default=None)

    # We do not persist uid, it is only used by dispute agents to guarantee an uid.
    uid: str = field(default_factory=lambda: str(uuid4()), init=False)  # transient

    payout_tx_confirms: int = field(default=-1)  # transient

    payout_done: bool = field(default=False)  # transient

    badge_count: int = field(default=0)  # transient

    file_transfer_session: Optional["FileTransferSession"] = field(
        default=None
    )  # transient
    # TODO: implement cached_deposit_tx ?
    cached_deposit_tx: list = field(default_factory=list)  # transient
    
    def __post_init__(self):
        self.id = self.trade_id + "_" + self.trader_id
        self.refresh_alert_level(True)

    def create_or_get_file_transfer_receiver(
        self,
        network_node: "NetworkNode",
        peer_node_address: "NodeAddress",
        callback: "FileTransferSession.FtpCallback",
    ) -> "FileTransferReceiver":
        # the receiver stores its state temporarily here in the dispute
        # this method gets called to retrieve the session each time a part of the log files is received
        if self.file_transfer_session is None:
            self.file_transfer_session = FileTransferReceiver(
                network_node=network_node,
                peer_node_address=peer_node_address,
                trade_id=self.trade_id,
                trader_id=self.trader_id,
                trader_role=self.get_role_string_for_log_file(),
                callback=callback,
            )
        return self.file_transfer_session

    def create_file_transfer_sender(
        self,
        network_node: "NetworkNode",
        peer_node_address: "NodeAddress",
        callback: "FileTransferSession.FtpCallback",
    ) -> "FileTransferSender":
        return FileTransferSender(
            network_node=network_node,
            peer_node_address=peer_node_address,
            trade_id=self.trade_id,
            trader_id=self.trader_id,
            trader_role=self.get_role_string_for_log_file(),
            callback=callback,
            is_test=False,
        )
        
    def to_proto_message(self):
        message = protobuf.Dispute(
            trade_id=self.trade_id,
            trader_id=self.trader_id,
            dispute_opener_is_buyer=self.dispute_opener_is_buyer,
            dispute_opener_is_maker=self.dispute_opener_is_maker,
            trader_pub_key_ring=self.trader_pub_key_ring.to_proto_message(),
            trade_date=self.trade_date,
            trade_period_end=self.trade_period_end,
            contract=self.contract.to_proto_message(),
            contract_as_json=self.contract_as_json,
            agent_pub_key_ring=self.agent_pub_key_ring.to_proto_message(),
            is_support_ticket=self.is_support_ticket,
            chat_message=[m.to_proto_network_envelope().chat_message for m in self.chat_messages],
            is_closed=self.is_closed,
            opening_date=self.openning_date,
            state=DisputeState.to_proto_message(self.dispute_state),
            id=self.id,
            burning_man_selection_height=self.burning_man_selection_height,
            trade_tx_fee=self.trade_tx_fee,
            
            contract_hash=self.contract_hash,
            deposit_tx_serialized=self.deposit_tx_serialized,
            payout_tx_serialized=self.payout_tx_serialized,
            deposit_tx_id=self.deposit_tx_id,
            payout_tx_id=self.payout_tx_id,
            dispute_payout_tx_id=self.dispute_payout_tx_id,
            maker_contract_signature=self.maker_contract_signature,
            taker_contract_signature=self.taker_contract_signature,
            dispute_result=self.dispute_result.to_proto_message() if self.dispute_result else None,
            support_type=SupportType.to_proto_message(self.support_type) if self.support_type else None,
            mediators_dispute_result=self.mediators_dispute_result,
            delayed_payout_tx_id=self.delayed_payout_tx_id,
            donation_address_of_delayed_payout_tx=self.donation_address_of_delayed_payout_tx,
        )
        return message
    
    @staticmethod
    def from_proto(proto: protobuf.Dispute, core_proto_resolver: "CoreProtoResolver"):
        dispute = Dispute(
            openning_date=proto.opening_date,
            trade_id=proto.trade_id,
            trader_id=proto.trader_id,
            dispute_opener_is_buyer=proto.dispute_opener_is_buyer,
            dispute_opener_is_maker=proto.dispute_opener_is_maker,
            trader_pub_key_ring=PubKeyRing.from_proto(proto.trader_pub_key_ring),
            trade_date=proto.trade_date,
            trade_period_end=proto.trade_period_end,
            contract=Contract.from_proto(proto.contract, core_proto_resolver),
            contract_hash=proto.contract_hash,
            deposit_tx_serialized=proto.deposit_tx_serialized,
            payout_tx_serialized=proto.payout_tx_serialized,
            deposit_tx_id=ProtoUtil.string_or_none_from_proto(proto.deposit_tx_id),
            payout_tx_id=ProtoUtil.string_or_none_from_proto(proto.payout_tx_id),
            contract_as_json=proto.contract_as_json,
            maker_contract_signature=ProtoUtil.string_or_none_from_proto(proto.maker_contract_signature),
            taker_contract_signature=ProtoUtil.string_or_none_from_proto(proto.taker_contract_signature),
            agent_pub_key_ring=proto.agent_pub_key_ring,
            is_support_ticket=proto.is_support_ticket,
            support_type=SupportType.from_proto(proto.support_type),
            burning_man_selection_height=proto.burning_man_selection_height,
            trade_tx_fee=proto.trade_tx_fee,
        )
        
        if proto.extra_data:
            dispute.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(proto.extra_data)
        
        if proto.chat_message:
            for chat_message in proto.chat_message:
                dispute.chat_messages.append(ChatMessage.from_payload_proto(chat_message))
                
        if proto.dispute_result:
            dispute.dispute_result = DisputeResult.from_proto(proto.dispute_result)
        
        dispute.dispute_payout_tx_id = ProtoUtil.string_or_none_from_proto(proto.dispute_payout_tx_id)
        
        if proto.mediators_dispute_result:
            dispute.mediators_dispute_result = proto.mediators_dispute_result
            
        if proto.delayed_payout_tx_id:
            dispute.delayed_payout_tx_id = proto.delayed_payout_tx_id
        
        if proto.donation_address_of_delayed_payout_tx:
            dispute.donation_address_of_delayed_payout_tx = proto.donation_address_of_delayed_payout_tx
            
        if DisputeState.from_proto(proto.state) == DisputeState.NEEDS_UPGRADE:
            # old disputes did not have a state field, so choose an appropriate state:
            dispute.dispute_state = DisputeState.CLOSED if proto.is_closed else DisputeState.OPEN
            if dispute.dispute_state == DisputeState.CLOSED:
                # mark chat messages as read for pre-existing CLOSED disputes
                # otherwise at upgrade, all old disputes would have 1 unread chat message
                # because currently when a dispute is closed, the last chat message is not marked read
                for chat_message in dispute.chat_messages:
                    chat_message.was_displayed = True       
        else:
            dispute.dispute_state = DisputeState.from_proto(proto.state)
            
        dispute.refresh_alert_level(True)
        return dispute

    def add_and_persist_chat_message(self, chat_message: "ChatMessage"):
        if chat_message not in self.chat_messages:
            self.chat_messages.append(chat_message)
        else:
            logger.error("disputeDirectMessage already exists")
            
    def remove_all_chat_messages(self):
        if len(self.chat_messages) > 1:
            # removes all chat except the initial guidelines message.
            first_message_uid = self.chat_messages[0].uid
            self.chat_messages[:] = [msg for msg in self.chat_messages if msg.uid == first_message_uid]
            return True
        return False
            
    def maybe_clear_sensitive_data(self):
        change = ""
        if self.contract.maybe_clear_sensitive_data():
            change += "contract;"
        edited = self.contract.sanitize_contract_as_json(self.contract_as_json)
        if edited != self.contract_as_json:
            self.contract_as_json = edited
            change += "contractAsJson;"
        if self.remove_all_chat_messages():
            change += "chat messages;"
        if len(change) > 0:
            logger.info(f"cleared sensitive data from {change} of dispute for trade {get_short_id(self.trade_id)}")
        
    def re_open(self):
        self.dispute_state = DisputeState.REOPENED
    
    def set_closed(self):
        self.dispute_state = DisputeState.CLOSED
        
    def set_extra_data(self, key: str, value: str):
        if key is None or value is None:
            return
        if self.extra_data_map is None:
            self.extra_data_map = {}
        self.extra_data_map[key] = value
        
    def get_short_trade_id(self):
        return get_short_id(self.trade_id)
    
    def get_trade_date(self):
        return datetime.fromtimestamp(self.trade_date / 1000)
    
    def get_trade_period_end(self):
        return datetime.fromtimestamp(self.trade_period_end / 1000)
    
    def get_opening_date(self):
        return datetime.fromtimestamp(self.openning_date / 1000)
    
    @property
    def is_new(self) -> bool:
        return self.dispute_state == DisputeState.NEW
        
    @property
    def is_closed(self) -> bool:
        return self.dispute_state == DisputeState.CLOSED
    
    @property
    def is_result_proposed(self) -> bool:
        return self.dispute_state == DisputeState.RESULT_PROPOSED
    
    def refresh_alert_level(self, sender_flag: bool):
        # if the dispute is "new" that is 1 alert that has to be propagated upstrea
        # or if there are unread messages that is 1 alert that has to be propagated upstream
        if self.is_new or self.unread_message_count(sender_flag) > 0:
            self.badge_count = 1
        else:
            self.badge_count = 0
    
    def unread_message_count(self, sender_flag: bool):
        """
              return chatMessages.stream()
                .filter(m -> m.isSenderIsTrader() == senderFlag || m.isSystemMessage())
                .filter(m -> !m.isWasDisplayed())
                .count();"""
        count = 0
        if self.chat_messages is not None:
            for message in self.chat_messages:
                if (message.sender_is_trader == sender_flag or message.is_system_message) and not message.was_displayed:
                    count += 1
        return count
    
    def set_dispute_seen(self, sender_flag: bool):
        if self.dispute_state == DisputeState.NEW:
            self.dispute_state = DisputeState.OPEN
        self.refresh_alert_level(sender_flag)
    
    def set_chat_messages_seen(self, sender_flag: bool):
        for message in self.chat_messages:
            message.was_displayed = True
        self.refresh_alert_level(sender_flag)
        
    def get_role_string(self):
        if self.dispute_opener_is_maker:
            if self.dispute_opener_is_buyer:
                return Res.get("support.buyerOfferer")
            else:
                return Res.get("support.sellerOfferer")
        else:
            if self.dispute_opener_is_buyer:
                return Res.get("support.buyerTaker")
            else:
                return Res.get("support.sellerTaker")
    
    def get_role_string_for_log_file(self) -> str:
        return f"{'BUYER' if self.dispute_opener_is_buyer else 'SELLER'}_{'MAKER' if self.dispute_opener_is_maker else 'TAKER'}"

    def find_deposit_tx(self, btc_wallet_service):
        # TODO:
        raise NotImplementedError("find_deposit_tx not implemented")
    
    # Dispute agents might receive disputes created before activation date.
    # By checking if burningManSelectionHeight is > 0 we can detect if the trade was created with
    # the new burningmen receivers or with legacy BM.
    def is_using_legacy_burning_man(self):
        return self.burning_man_selection_height == 0

    def __str__(self):
            
        return (f"Dispute{{"
                f"\n     trade_id='{self.trade_id}'"
                f",\n     id='{self.id}'"
                f",\n     uid='{self.uid}'"
                f",\n     state={self.dispute_state}"
                f",\n     trader_id={self.trader_id}"
                f",\n     dispute_opener_is_buyer={self.dispute_opener_is_buyer}"
                f",\n     dispute_opener_is_maker={self.dispute_opener_is_maker}"
                f",\n     trader_pub_key_ring={self.trader_pub_key_ring}"
                f",\n     trade_date={self.trade_date}"
                f",\n     trade_period_end={self.trade_period_end}"
                f",\n     contract={self.contract}"
                f",\n     contract_hash={bytes_as_hex_string(self.contract_hash)}"
                f",\n     deposit_tx_serialized={bytes_as_hex_string(self.deposit_tx_serialized)}"
                f",\n     payout_tx_serialized={bytes_as_hex_string(self.payout_tx_serialized)}"
                f",\n     deposit_tx_id='{self.deposit_tx_id}'"
                f",\n     payout_tx_id='{self.payout_tx_id}'"
                f",\n     contract_as_json='{self.contract_as_json}'"
                f",\n     maker_contract_signature='{self.maker_contract_signature}'"
                f",\n     taker_contract_signature='{self.taker_contract_signature}'"
                f",\n     agent_pub_key_ring={self.agent_pub_key_ring}"
                f",\n     is_support_ticket={self.is_support_ticket}"
                f",\n     chat_messages={self.chat_messages}"
                f",\n     dispute_result={self.dispute_result}"
                f",\n     dispute_payout_tx_id='{self.dispute_payout_tx_id}'"
                f",\n     openning_date={self.openning_date}"
                f",\n     support_type={self.support_type}"
                f",\n     mediators_dispute_result='{self.mediators_dispute_result}'"
                f",\n     delayed_payout_tx_id='{self.delayed_payout_tx_id}'"
                f",\n     donation_address_of_delayed_payout_tx='{self.donation_address_of_delayed_payout_tx}'"
                f",\n     cached_deposit_tx='{self.cached_deposit_tx}'"
                f",\n     burning_man_selection_height='{self.burning_man_selection_height}'"
                f",\n     trade_tx_fee='{self.trade_tx_fee}'"
                "\n}}")

