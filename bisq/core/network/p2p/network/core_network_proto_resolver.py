
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
from bisq.core.network.p2p.network.core_proto_resolver import CoreProtoResolver
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
from bisq.core.support.dispute.arbitration.messages.open_new_dispute_message import OpenNewDisputeMessage
from bisq.core.support.dispute.arbitration.messages.peer_published_dispute_payout_tx_message import PeerPublishedDisputePayoutTxMessage
from bisq.core.support.dispute.mediation.mediator.mediator import Mediator
from bisq.core.support.dispute.messages.dispute_result_message import DisputeResultMessage
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
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_payload import NetworkPayload

logger = get_logger(__name__)

# Singleton?
class CoreNetworkProtoResolver(CoreProtoResolver, NetworkProtoResolver):
    def __init__(self, clock: Clock):
        self.clock = clock

    def from_proto(self, proto: Union['protobuf.NetworkEnvelope', 'protobuf.StorageEntryWrapper', 'protobuf.StoragePayload']) -> 'NetworkPayload':
        """
        DAO related stuff and BTC node related stuff are not implemented.
        """
        if proto is None:
            logger.error("CoreNetworkProtoResolver.fromProto: proto is null")
            raise ProtobufferException("proto is null")
        
        if isinstance(proto, protobuf.NetworkEnvelope):
            message_version = proto.message_version
            match proto.WhichOneof("message"):
                case "preliminary_get_data_request":
                    return PreliminaryGetDataRequest.from_proto(proto.preliminary_get_data_request, message_version)
                case "get_data_response":
                    return GetDataResponse.from_proto(proto.get_data_response, self, message_version)
                case "get_updated_data_request":
                    return GetUpdatedDataRequest.from_proto(proto.get_updated_data_request, message_version)
                case "get_peers_request":
                    return GetPeersRequest.from_proto(proto.get_peers_request, message_version)
                case "get_peers_response":
                    return GetPeersResponse.from_proto(proto.get_peers_response, message_version)
                case "ping":
                    return Ping.from_proto(proto.ping, message_version)
                case "pong":
                    return Pong.from_proto(proto.pong, message_version)
                case "file_transfer_part":
                    return FileTransferPart.from_proto(proto.file_transfer_part, message_version)
                case "offer_availability_request":
                    return OfferAvailabilityRequest.from_proto(proto.offer_availability_request, message_version)
                case "offer_availability_response":
                    return OfferAvailabilityResponse.from_proto(proto.offer_availability_response, message_version)
                case "refresh_offer_message":
                    return RefreshOfferMessage.from_proto(proto.refresh_offer_message, message_version)
                case "add_data_message":
                    return AddDataMessage.from_proto(proto.add_data_message, self, message_version)
                case "remove_data_message":
                    return RemoveDataMessage.from_proto(proto.remove_data_message, self, message_version)
                case "remove_mailbox_data_message":
                    return RemoveMailboxDataMessage.from_proto(proto.remove_mailbox_data_message, self, message_version)
                case "close_connection_message":
                    return CloseConnectionMessage.from_proto(proto.close_connection_message, message_version)
                case "prefixed_sealed_and_signed_message":
                    return PrefixedSealedAndSignedMessage.from_proto(proto.prefixed_sealed_and_signed_message, message_version)
                # trade protocol messages
                case "refresh_trade_state_request":
                    return RefreshTradeStateRequest.from_proto(proto.refresh_trade_state_request, message_version)
                case "inputs_for_deposit_tx_request":
                    return InputsForDepositTxRequest.from_proto(proto.inputs_for_deposit_tx_request, self, message_version)
                case "inputs_for_deposit_tx_response":
                    return InputsForDepositTxResponse.from_proto(proto.inputs_for_deposit_tx_response, self, message_version)
                case "deposit_tx_message":
                    return DepositTxMessage.from_proto(proto.deposit_tx_message, message_version)
                case "delayed_payout_tx_signature_request":
                    return DelayedPayoutTxSignatureRequest.from_proto(proto.delayed_payout_tx_signature_request, message_version)
                case "delayed_payout_tx_signature_response":
                    return DelayedPayoutTxSignatureResponse.from_proto(proto.delayed_payout_tx_signature_response, message_version)
                case "deposit_tx_and_delayed_payout_tx_message":
                    return DepositTxAndDelayedPayoutTxMessage.from_proto(proto.deposit_tx_and_delayed_payout_tx_message, self, message_version)
                case "share_buyer_payment_account_message":
                    return ShareBuyerPaymentAccountMessage.from_proto(proto.share_buyer_payment_account_message, self, message_version)
                # case "sellers_bsq_swap_request":
                #     return SellersBsqSwapRequest.from_proto(proto.sellers_bsq_swap_request, message_version)
                # case "buyers_bsq_swap_request":
                #     return BuyersBsqSwapRequest.from_proto(proto.buyers_bsq_swap_request, message_version)
                # case "bsq_swap_tx_inputs_message":
                #     return BsqSwapTxInputsMessage.from_proto(proto.bsq_swap_tx_inputs_message, message_version)
                # case "bsq_swap_finalize_tx_request":
                #     return BsqSwapFinalizeTxRequest.from_proto(proto.bsq_swap_finalize_tx_request, message_version)
                # case "bsq_swap_finalized_tx_message":
                #     return BsqSwapFinalizedTxMessage.from_proto(proto.bsq_swap_finalized_tx_message, message_version)
                case "counter_currency_transfer_started_message":
                    return CounterCurrencyTransferStartedMessage.from_proto(proto.counter_currency_transfer_started_message, message_version)
                case "payout_tx_published_message":
                    return PayoutTxPublishedMessage.from_proto(proto.payout_tx_published_message, message_version)
                case "peer_published_delayed_payout_tx_message":
                    return PeerPublishedDelayedPayoutTxMessage.from_proto(proto.peer_published_delayed_payout_tx_message, message_version)
                case "trader_signed_witness_message":
                    return TraderSignedWitnessMessage.from_proto(proto.trader_signed_witness_message, message_version)
                case "mediated_payout_tx_signature_message":
                    return MediatedPayoutTxSignatureMessage.from_proto(proto.mediated_payout_tx_signature_message, message_version)
                case "mediated_payout_tx_published_message":
                    return MediatedPayoutTxPublishedMessage.from_proto(proto.mediated_payout_tx_published_message, message_version)
                case "open_new_dispute_message":
                    return OpenNewDisputeMessage.from_proto(proto.open_new_dispute_message, self, message_version)
                case "peer_opened_dispute_message":
                    return PeerOpenedDisputeMessage.from_proto(proto.peer_opened_dispute_message, self, message_version)
                case "chat_message":
                    return ChatMessage.from_proto(proto.chat_message, message_version)
                case "dispute_result_message":
                    return DisputeResultMessage.from_proto(proto.dispute_result_message, message_version)
                case "peer_published_dispute_payout_tx_message":
                    return PeerPublishedDisputePayoutTxMessage.from_proto(proto.peer_published_dispute_payout_tx_message, message_version)
                case "private_notification_message":
                    return PrivateNotificationMessage.from_proto(proto.private_notification_message, message_version)
                # case "get_blocks_request":
                #     return GetBlocksRequest.from_proto(proto.get_blocks_request, message_version)
                # case "get_blocks_response":
                #     return GetBlocksResponse.from_proto(proto.get_blocks_response, message_version)
                # case "new_block_broadcast_message":
                #     return NewBlockBroadcastMessage.from_proto(proto.new_block_broadcast_message, message_version)
                case "add_persistable_network_payload_message":
                    return AddPersistableNetworkPayloadMessage.from_proto(proto.add_persistable_network_payload_message, self, message_version)
                case "ack_message":
                    return AckMessage.from_proto(proto.ack_message, message_version)
                # case "republish_governance_data_request":
                #     return RepublishGovernanceDataRequest.from_proto(proto.republish_governance_data_request, message_version)
                # case "new_dao_state_hash_message":
                #     return NewDaoStateHashMessage.from_proto(proto.new_dao_state_hash_message, message_version)
                # case "get_dao_state_hashes_request":
                #     return GetDaoStateHashesRequest.from_proto(proto.get_dao_state_hashes_request, message_version)
                # case "get_dao_state_hashes_response":
                #     return GetDaoStateHashesResponse.from_proto(proto.get_dao_state_hashes_response, message_version)
                # case "new_proposal_state_hash_message":
                #     return NewProposalStateHashMessage.from_proto(proto.new_proposal_state_hash_message, message_version)
                # case "get_proposal_state_hashes_request":
                #     return GetProposalStateHashesRequest.from_proto(proto.get_proposal_state_hashes_request, message_version)
                # case "get_proposal_state_hashes_response":
                #     return GetProposalStateHashesResponse.from_proto(proto.get_proposal_state_hashes_response, message_version)
                # case "new_blind_vote_state_hash_message":
                #     return NewBlindVoteStateHashMessage.from_proto(proto.new_blind_vote_state_hash_message, message_version)
                # case "get_blind_vote_state_hashes_request":
                #     return GetBlindVoteStateHashesRequest.from_proto(proto.get_blind_vote_state_hashes_request, message_version)
                # case "get_blind_vote_state_hashes_response":
                #     return GetBlindVoteStateHashesResponse.from_proto(proto.get_blind_vote_state_hashes_response, message_version)
                case "bundle_of_envelopes":
                    return BundleOfEnvelopes.from_proto(proto.bundle_of_envelopes, self, message_version)
                case "get_inventory_request":
                    return GetInventoryRequest.from_proto(proto.get_inventory_request, message_version)
                case "get_inventory_response":
                    return GetInventoryResponse.from_proto(proto.get_inventory_response, message_version)
                # case "get_accounting_blocks_request":
                #     return GetAccountingBlocksRequest.from_proto(proto.get_accounting_blocks_request, message_version)
                # case "get_accounting_blocks_response":
                #     return GetAccountingBlocksResponse.from_proto(proto.get_accounting_blocks_response, message_version)
                # case "new_accounting_block_broadcast_message":
                #     return NewAccountingBlockBroadcastMessage.from_proto(proto.new_accounting_block_broadcast_message, message_version)
                case _:
                    raise ProtobufferException(f"Unknown proto message case (PB.NetworkEnvelope). messageCase={proto.WhichOneof("message")}; proto raw data={proto}")
        elif isinstance(proto, protobuf.StorageEntryWrapper):
            match proto.WhichOneof("message"):
                case "protected_mailbox_storage_entry":
                    return ProtectedMailboxStorageEntry.from_proto(proto.protected_mailbox_storage_entry, self)
                case "protected_storage_entry":
                    return ProtectedStorageEntry.from_proto(proto.protected_storage_entry, self)
                case _:
                    raise ProtobufferException(f"Unknown proto message case(PB.StorageEntryWrapper). messageCase={proto.WhichOneof('message')}; proto raw data={proto}")
        elif isinstance(proto, protobuf.StoragePayload):
            match proto.WhichOneof("message"):
                case "alert":
                    return Alert.from_proto(proto.alert)
                case "arbitrator":
                    return Arbitrator.from_proto(proto.arbitrator)
                case "mediator":
                    return Mediator.from_proto(proto.mediator)
                case "refund_agent":
                    return RefundAgent.from_proto(proto.refund_agent)
                case "filter":
                    return Filter.from_proto(proto.filter)
                case "mailbox_storage_payload":
                    return MailboxStoragePayload.from_proto(proto.mailbox_storage_payload)
                case "offer_payload":
                    return OfferPayload.from_proto(proto.offer_payload)
                case "bsq_swap_offer_payload":
                    return BsqSwapOfferPayload.from_proto(proto.bsq_swap_offer_payload)
                # case "temp_proposal_payload":
                #     return TempProposalPayload.from_proto(proto.temp_proposal_payload)
                case _:
                    raise ProtobufferException(f"Unknown proto message case (PB.StoragePayload). messageCase={proto.WhichOneof('message')}; proto raw data={proto}")
        else:
            return super().from_proto(proto)
