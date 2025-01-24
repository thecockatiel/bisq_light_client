from collections.abc import Callable
from typing import TYPE_CHECKING, Union
from bisq.core.alert.alert import Alert
from bisq.core.alert.private_notification_message import PrivateNotificationMessage
from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.bundle_of_envelopes import BundleOfEnvelopes
from bisq.core.network.p2p.close_connection_message import CloseConnectionMessage
from bisq.core.network.p2p.file_transfer_part import FileTransferPart
from bisq.core.network.p2p.inventory.messages.get_inventory_request import GetInventoryRequest
from bisq.core.network.p2p.inventory.messages.get_inventory_response import GetInventoryResponse
from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
from bisq.core.network.p2p.peers.getdata.messages.get_data_response import GetDataResponse
from bisq.core.network.p2p.peers.getdata.messages.get_updated_data_request import GetUpdatedDataRequest
from bisq.core.network.p2p.peers.getdata.messages.preliminary_get_data_request import PreliminaryGetDataRequest
from bisq.core.network.p2p.peers.keepalive.messages.ping import Ping
from bisq.core.network.p2p.peers.keepalive.messages.pong import Pong
from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_request import GetPeersRequest
from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_response import GetPeersResponse
from bisq.core.network.p2p.prefixed_sealed_and_signed_message import PrefixedSealedAndSignedMessage
from bisq.core.network.p2p.storage.messages.add_data_message import AddDataMessage
from bisq.core.network.p2p.storage.messages.add_persistable_network_payload_message import AddPersistableNetworkPayloadMessage
from bisq.core.network.p2p.storage.messages.refresh_offer_message import RefreshOfferMessage
from bisq.core.network.p2p.storage.messages.remove_data_message import RemoveDataMessage
from bisq.core.network.p2p.storage.messages.remove_mailbox_data_message import RemoveMailboxDataMessage
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import MailboxStoragePayload
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import ProtectedMailboxStorageEntry
from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
from bisq.core.offer.availability.messages.offer_availability_request import OfferAvailabilityRequest
from bisq.core.offer.availability.messages.offer_availability_response import OfferAvailabilityResponse
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.offer.bsq_swap.bsq_swap_offer_payload import BsqSwapOfferPayload
from bisq.core.support.dispute.arbitration.arbitrator.arbitrator import Arbitrator
from bisq.core.support.dispute.arbitration.messages.peer_published_dispute_payout_tx_message import PeerPublishedDisputePayoutTxMessage
from bisq.core.support.dispute.mediation.mediator.mediator import Mediator
from bisq.core.support.dispute.messages.dispute_result_message import DisputeResultMessage
from bisq.core.support.dispute.messages.open_new_dispute_message import OpenNewDisputeMessage
from bisq.core.support.dispute.messages.peer_opened_dispute_message import PeerOpenedDisputeMessage
from bisq.core.support.messages.chat_messsage import ChatMessage
from bisq.core.support.refund.refundagent.refund_agent import RefundAgent
from bisq.core.trade.protocol.bisq_v1.messages.counter_currency_transfer_started_message import CounterCurrencyTransferStartedMessage
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_request import DelayedPayoutTxSignatureRequest
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_response import DelayedPayoutTxSignatureResponse
from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import DepositTxAndDelayedPayoutTxMessage
from bisq.core.trade.protocol.bisq_v1.messages.deposit_tx_message import DepositTxMessage
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import InputsForDepositTxRequest
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_response import InputsForDepositTxResponse
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_published_message import MediatedPayoutTxPublishedMessage
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_signature_message import MediatedPayoutTxSignatureMessage
from bisq.core.trade.protocol.bisq_v1.messages.payout_tx_published_message import PayoutTxPublishedMessage
from bisq.core.trade.protocol.bisq_v1.messages.peer_published_delayed_payout_tx_message import PeerPublishedDelayedPayoutTxMessage
from bisq.core.trade.protocol.bisq_v1.messages.refresh_trade_state_request import RefreshTradeStateRequest
from bisq.core.trade.protocol.bisq_v1.messages.share_buyer_payment_account_message import ShareBuyerPaymentAccountMessage
from bisq.core.filter.filter import Filter
from bisq.core.trade.protocol.bisq_v1.messages.trader_signed_witness_message import TraderSignedWitnessMessage
from bisq.common.setup.log_setup import get_logger
from utils.clock import Clock
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_payload import NetworkPayload
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope

logger = get_logger(__name__)

proto_network_envelope_map: dict[str, Callable[[protobuf.NetworkEnvelope, "CoreNetworkProtoResolver", int], 'NetworkEnvelope']]  = {
    "preliminary_get_data_request": lambda proto, resolver, message_version: PreliminaryGetDataRequest.from_proto(proto.preliminary_get_data_request, message_version),
    "get_data_response": lambda proto, resolver, message_version: GetDataResponse.from_proto(proto.get_data_response, resolver, message_version),
    "get_updated_data_request": lambda proto, resolver, message_version: GetUpdatedDataRequest.from_proto(proto.get_updated_data_request, message_version),
    
    "get_peers_request": lambda proto, resolver, message_version: GetPeersRequest.from_proto(proto.get_peers_request, message_version),
    "get_peers_response": lambda proto, resolver, message_version: GetPeersResponse.from_proto(proto.get_peers_response, message_version),
    "ping": lambda proto, resolver, message_version: Ping.from_proto(proto.ping, message_version),
    "pong": lambda proto, resolver, message_version: Pong.from_proto(proto.pong, message_version),
    "file_transfer_part": lambda proto, resolver, message_version: FileTransferPart.from_proto(proto.file_transfer_part, message_version),
    
    "offer_availability_request": lambda proto, resolver, message_version: OfferAvailabilityRequest.from_proto(proto.offer_availability_request, message_version),
    "offer_availability_response": lambda proto, resolver, message_version: OfferAvailabilityResponse.from_proto(proto.offer_availability_response, message_version),
    "refresh_offer_message": lambda proto, resolver, message_version: RefreshOfferMessage.from_proto(proto.refresh_offer_message, message_version),
    
    "add_data_message": lambda proto, resolver, message_version: AddDataMessage.from_proto(proto.add_data_message, resolver, message_version),
    "remove_data_message": lambda proto, resolver, message_version: RemoveDataMessage.from_proto(proto.remove_data_message, resolver, message_version),
    "remove_mailbox_data_message": lambda proto, resolver, message_version: RemoveMailboxDataMessage.from_proto(proto.remove_mailbox_data_message, resolver, message_version),
    
    "close_connection_message": lambda proto, resolver, message_version: CloseConnectionMessage.from_proto(proto.close_connection_message, message_version),
    "prefixed_sealed_and_signed_message": lambda proto, resolver, message_version: PrefixedSealedAndSignedMessage.from_proto(proto.prefixed_sealed_and_signed_message, message_version),
    
    # trade protocol messages
    "refresh_trade_state_request": lambda proto, resolver, message_version: RefreshTradeStateRequest.from_proto(proto.refresh_trade_state_request, message_version),
    "inputs_for_deposit_tx_request": lambda proto, resolver, message_version: InputsForDepositTxRequest.from_proto(proto.inputs_for_deposit_tx_request, resolver, message_version),
    "inputs_for_deposit_tx_response": lambda proto, resolver, message_version: InputsForDepositTxResponse.from_proto(proto.inputs_for_deposit_tx_response, resolver, message_version),
    "deposit_tx_message": lambda proto, resolver, message_version: DepositTxMessage.from_proto(proto.deposit_tx_message, message_version),
    "delayed_payout_tx_signature_request": lambda proto, resolver, message_version: DelayedPayoutTxSignatureRequest.from_proto(proto.delayed_payout_tx_signature_request, message_version),
    "delayed_payout_tx_signature_response": lambda proto, resolver, message_version: DelayedPayoutTxSignatureResponse.from_proto(proto.delayed_payout_tx_signature_response, message_version),
    "deposit_tx_and_delayed_payout_tx_message": lambda proto, resolver, message_version: DepositTxAndDelayedPayoutTxMessage.from_proto(proto.deposit_tx_and_delayed_payout_tx_message, resolver, message_version),
    "share_buyer_payment_account_message": lambda proto, resolver, message_version: ShareBuyerPaymentAccountMessage.from_proto(proto.share_buyer_payment_account_message, resolver, message_version),
    
    # "sellers_bsq_swap_request": lambda proto, resolver, message_version: SellersBsqSwapRequest.from_proto(proto.sellers_bsq_swap_request, message_version),
    # "buyers_bsq_swap_request": lambda proto, resolver, message_version: BuyersBsqSwapRequest.from_proto(proto.buyers_bsq_swap_request, message_version),
    # "bsq_swap_tx_inputs_message": lambda proto, resolver, message_version: BsqSwapTxInputsMessage.from_proto(proto.bsq_swap_tx_inputs_message, message_version),
    # "bsq_swap_finalize_tx_request": lambda proto, resolver, message_version: BsqSwapFinalizeTxRequest.from_proto(proto.bsq_swap_finalize_tx_request, message_version),
    # "bsq_swap_finalized_tx_message": lambda proto, resolver, message_version: BsqSwapFinalizedTxMessage.from_proto(proto.bsq_swap_finalized_tx_message, message_version),
    
    "counter_currency_transfer_started_message": lambda proto, resolver, message_version: CounterCurrencyTransferStartedMessage.from_proto(proto.counter_currency_transfer_started_message, message_version),
    
    "payout_tx_published_message": lambda proto, resolver, message_version: PayoutTxPublishedMessage.from_proto(proto.payout_tx_published_message, message_version),
    "peer_published_delayed_payout_tx_message": lambda proto, resolver, message_version: PeerPublishedDelayedPayoutTxMessage.from_proto(proto.peer_published_delayed_payout_tx_message, message_version),
    "trader_signed_witness_message": lambda proto, resolver, message_version: TraderSignedWitnessMessage.from_proto(proto.trader_signed_witness_message, message_version),
    
    "mediated_payout_tx_signature_message": lambda proto, resolver, message_version: MediatedPayoutTxSignatureMessage.from_proto(proto.mediated_payout_tx_signature_message, message_version),
    "mediated_payout_tx_published_message": lambda proto, resolver, message_version: MediatedPayoutTxPublishedMessage.from_proto(proto.mediated_payout_tx_published_message, message_version),
    
    "open_new_dispute_message": lambda proto, resolver, message_version: OpenNewDisputeMessage.from_proto(proto.open_new_dispute_message, resolver, message_version),
    "peer_opened_dispute_message": lambda proto, resolver, message_version: PeerOpenedDisputeMessage.from_proto(proto.peer_opened_dispute_message, resolver, message_version),
    "chat_message": lambda proto, resolver, message_version: ChatMessage.from_proto(proto.chat_message, message_version),
    "dispute_result_message": lambda proto, resolver, message_version: DisputeResultMessage.from_proto(proto.dispute_result_message, message_version),
    "peer_published_dispute_payout_tx_message": lambda proto, resolver, message_version: PeerPublishedDisputePayoutTxMessage.from_proto(proto.peer_published_dispute_payout_tx_message, message_version),
    
    "private_notification_message": lambda proto, resolver, message_version: PrivateNotificationMessage.from_proto(proto.private_notification_message, message_version),
    
    # "get_blocks_request": lambda proto, resolver, message_version: GetBlocksRequest.from_proto(proto.get_blocks_request, message_version),
    # "get_blocks_response": lambda proto, resolver, message_version: GetBlocksResponse.from_proto(proto.get_blocks_response, message_version),
    # "new_block_broadcast_message": lambda proto, resolver, message_version: NewBlockBroadcastMessage.from_proto(proto.new_block_broadcast_message, message_version),
    "add_persistable_network_payload_message": lambda proto, resolver, message_version: AddPersistableNetworkPayloadMessage.from_proto(proto.add_persistable_network_payload_message, resolver, message_version),
    "ack_message": lambda proto, resolver, message_version: AckMessage.from_proto(proto.ack_message, message_version),
    # "republish_governance_data_request": lambda proto, resolver, message_version: RepublishGovernanceDataRequest.from_proto(proto.republish_governance_data_request, message_version),
    
    # "new_dao_state_hash_message": lambda proto, resolver, message_version: NewDaoStateHashMessage.from_proto(proto.new_dao_state_hash_message, message_version),
    # "get_dao_state_hashes_request": lambda proto, resolver, message_version: GetDaoStateHashesRequest.from_proto(proto.get_dao_state_hashes_request, message_version),
    # "get_dao_state_hashes_response": lambda proto, resolver, message_version: GetDaoStateHashesResponse.from_proto(proto.get_dao_state_hashes_response, message_version),
    
    # "new_proposal_state_hash_message": lambda proto, resolver, message_version: NewProposalStateHashMessage.from_proto(proto.new_proposal_state_hash_message, message_version),
    # "get_proposal_state_hashes_request": lambda proto, resolver, message_version: GetProposalStateHashesRequest.from_proto(proto.get_proposal_state_hashes_request, message_version),
    # "get_proposal_state_hashes_response": lambda proto, resolver, message_version: GetProposalStateHashesResponse.from_proto(proto.get_proposal_state_hashes_response, message_version),
    
    # "new_blind_vote_state_hash_message": lambda proto, resolver, message_version: NewBlindVoteStateHashMessage.from_proto(proto.new_blind_vote_state_hash_message, message_version),
    # "get_blind_vote_state_hashes_request": lambda proto, resolver, message_version: GetBlindVoteStateHashesRequest.from_proto(proto.get_blind_vote_state_hashes_request, message_version),
    # "get_blind_vote_state_hashes_response": lambda proto, resolver, message_version: GetBlindVoteStateHashesResponse.from_proto(proto.get_blind_vote_state_hashes_response, message_version),
    
    "bundle_of_envelopes": lambda proto, resolver, message_version: BundleOfEnvelopes.from_proto(proto.bundle_of_envelopes, resolver, message_version),
    
    "get_inventory_request": lambda proto, resolver, message_version: GetInventoryRequest.from_proto(proto.get_inventory_request, message_version),
    "get_inventory_response": lambda proto, resolver, message_version: GetInventoryResponse.from_proto(proto.get_inventory_response, message_version),
    
    # "get_accounting_blocks_request": lambda proto, resolver, message_version: GetAccountingBlocksRequest.from_proto(proto.get_accounting_blocks_request, message_version),
    # "get_accounting_blocks_response": lambda proto, resolver, message_version: GetAccountingBlocksResponse.from_proto(proto.get_accounting_blocks_response, message_version),
    # "new_accounting_block_broadcast_message": lambda proto, resolver, message_version: NewAccountingBlockBroadcastMessage.from_proto(proto.new_accounting_block_broadcast_message, message_version),
}

proto_storage_entry_wrapper_map: dict[str, Callable[[protobuf.StorageEntryWrapper, "CoreNetworkProtoResolver", int], 'NetworkPayload']] = {
    "protected_mailbox_storage_entry": lambda proto, resolver: ProtectedMailboxStorageEntry.from_proto(proto.protected_mailbox_storage_entry, resolver),
    "protected_storage_entry": lambda proto, resolver: ProtectedStorageEntry.from_proto(proto.protected_storage_entry, resolver),
}

proto_storage_payload_map: dict[str, Callable[[protobuf.StoragePayload], 'NetworkPayload']] = {
    "alert": lambda proto: Alert.from_proto(proto.alert),
    "arbitrator": lambda proto: Arbitrator.from_proto(proto.arbitrator),
    "mediator": lambda proto: Mediator.from_proto(proto.mediator),
    "refund_agent": lambda proto: RefundAgent.from_proto(proto.refund_agent),
    "filter": lambda proto: Filter.from_proto(proto.filter),
    "mailbox_storage_payload": lambda proto: MailboxStoragePayload.from_proto(proto.mailbox_storage_payload),
    "offer_payload": lambda proto: OfferPayload.from_proto(proto.offer_payload),
    "bsq_swap_offer_payload": lambda proto: BsqSwapOfferPayload.from_proto(proto.bsq_swap_offer_payload),
    # "temp_proposal_payload": lambda proto: TempProposalPayload.from_proto(proto.temp_proposal_payload),
}

# Singleton?
class CoreNetworkProtoResolver(CoreProtoResolver, NetworkProtoResolver):
    def __init__(self, clock: Clock):
        self.clock = clock
        
    def get_clock(self):
        return self.clock

    def from_proto(self, proto: Union['protobuf.NetworkEnvelope', 'protobuf.StorageEntryWrapper', 'protobuf.StoragePayload']) -> Union['NetworkPayload', 'NetworkEnvelope']:
        """
        DAO related stuff and BTC node related stuff are not implemented.
        """
        if proto is None:
            logger.error("CoreNetworkProtoResolver.fromProto: proto is null")
            raise ProtobufferException("proto is null")
        
        if isinstance(proto, protobuf.NetworkEnvelope):
            message_version = proto.message_version
            message_type = proto.WhichOneof("message")
            if message_type in proto_network_envelope_map:
                return proto_network_envelope_map[message_type](proto, self, message_version)
            else:
                raise ProtobufferException(f"Unknown proto message case (PB.NetworkEnvelope). messageCase={message_type}; proto raw data={proto}")
        elif isinstance(proto, protobuf.StorageEntryWrapper):
            message_type = proto.WhichOneof("message")
            if message_type in proto_storage_entry_wrapper_map:
                return proto_storage_entry_wrapper_map[message_type](proto, self)
            else:
                raise ProtobufferException(f"Unknown proto message case(PB.StorageEntryWrapper). messageCase={message_type}; proto raw data={proto}")
        elif isinstance(proto, protobuf.StoragePayload):
            message_type = proto.WhichOneof("message")
            if message_type in proto_storage_payload_map:
                return proto_storage_payload_map[message_type](proto)
            else:
                raise ProtobufferException(f"Unknown proto message case (PB.StoragePayload). messageCase={message_type}; proto raw data={proto}")
        else:
            return super().from_proto(proto)
