from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.navigation_path import NavigationPath
from bisq.common.protocol.persistable.persistence_proto_resolver import PersistenceProtoResolver
from bisq.common.setup.log_setup import get_logger
from bisq.core.account.sign.signed_witness_store import SignedWitnessStore
from bisq.core.account.witness.account_age_witness_store import AccountAgeWitnessStore
from bisq.core.network.p2p.mailbox.ignored_mailbox_map import IgnoredMailboxMap
from bisq.core.network.p2p.mailbox.mailbox_message_list import MailboxMessageList
from bisq.core.network.p2p.peers.peerexchange.peer_list import PeerList
from bisq.core.network.p2p.persistence.removed_payloads_map import RemovedPayloadsMap
from bisq.core.network.p2p.storage.sequence_number_map import SequenceNumberMap
from bisq.core.payment.payment_account_list import PaymentAccountList
from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.core.support.dispute.arbitration.arbitration_dispute_list import ArbitrationDisputeList
from bisq.core.support.dispute.mediation.mediation_dispute_list import MediationDisputeList
from bisq.core.support.refund.refund_dispute_list import RefundDisputeList
from bisq.core.user.user_payload import UserPayload
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from utils.clock import Clock

logger = get_logger(__name__)

class CorePersistenceProtoResolver(CoreProtoResolver, PersistenceProtoResolver):
    def __init__(self, clock: "Clock", network_proto_resolver: "NetworkProtoResolver"):
        super().__init__(clock)
        self.network_proto_resolver = network_proto_resolver
        
    def from_proto(self, proto: protobuf.PersistableEnvelope) -> "PersistableEnvelope":
        if proto is None:
            logger.error("PersistableEnvelope.from_proto: PB.PersistableEnvelope is null")
            raise ProtobufferException("PB.PersistableEnvelope is null")
        
        match proto.WhichOneof("message"):
            case "sequence_number_map":
                return SequenceNumberMap.from_proto(proto.sequence_number_map)
            case "peer_list":
                return PeerList.from_proto(proto.peer_list)
            # case "address_entry_list":
            #     return AddressEntryList.from_proto(proto.address_entry_list)
            case "tradable_list":
                raise NotImplementedError("tradable_list not implemented yet") # TODO
                # return TradableList.from_proto(proto.tradable_list, self, btc_wallet_service.get())
            case "arbitration_dispute_list":
                return ArbitrationDisputeList.from_proto(proto.arbitration_dispute_list, self)
            case "mediation_dispute_list":
                return MediationDisputeList.from_proto(proto.mediation_dispute_list, self)
            case "refund_dispute_list":
                return RefundDisputeList.from_proto(proto.refund_dispute_list, self)
            case "preferences_payload":
                raise NotImplementedError("preferences_payload not implemented yet") # TODO
                # return PreferencesPayload.from_proto(proto.preferences_payload, self)
            case "user_payload":
                return UserPayload.from_proto(proto.user_payload, self)
            case "navigation_path":
                return NavigationPath.from_proto(proto.navigation_path)
            case "payment_account_list":
                return PaymentAccountList.from_proto(proto.payment_account_list, self)
            case "account_age_witness_store":
                return AccountAgeWitnessStore.from_proto(proto.account_age_witness_store)
            # case "trade_statistics2_store":
            #     return TradeStatistics2Store.from_proto(proto.trade_statistics2_store)
            # case "blind_vote_store":
            #     return BlindVoteStore.from_proto(proto.blind_vote_store)
            # case "proposal_store":
            #     return ProposalStore.from_proto(proto.proposal_store)
            # case "temp_proposal_store":
            #     return TempProposalStore.from_proto(proto.temp_proposal_store, self.network_proto_resolver)
            # case "my_proposal_list":
            #     return MyProposalList.from_proto(proto.my_proposal_list)
            # case "ballot_list":
            #     return BallotList.from_proto(proto.ballot_list)
            # case "my_vote_list":
            #     return MyVoteList.from_proto(proto.my_vote_list)
            # case "my_blind_vote_list":
            #     return MyBlindVoteList.from_proto(proto.my_blind_vote_list)
            # case "dao_state_store":
            #     return DaoStateStore.from_proto(proto.dao_state_store)
            # case "my_reputation_list":
            #     return MyReputationList.from_proto(proto.my_reputation_list)
            # case "my_proof_of_burn_list":
            #     return MyProofOfBurnList.from_proto(proto.my_proof_of_burn_list)
            # case "unconfirmed_bsq_change_output_list":
            #     return UnconfirmedBsqChangeOutputList.from_proto(proto.unconfirmed_bsq_change_output_list)
            case "signed_witness_store":
                return SignedWitnessStore.from_proto(proto.signed_witness_store)
            # case "trade_statistics3_store":
            #     return TradeStatistics3Store.from_proto(proto.trade_statistics3_store)
            case "mailbox_message_list":
                return MailboxMessageList.from_proto(proto.mailbox_message_list, self.network_proto_resolver)
            case "ignored_mailbox_map":
                return IgnoredMailboxMap.from_proto(proto.ignored_mailbox_map)
            case "removed_payloads_map":
                return RemovedPayloadsMap.from_proto(proto.removed_payloads_map)
            # case "bsq_block_store":
            #     return BsqBlockStore.from_proto(proto.bsq_block_store)
            # case "burning_man_accounting_store":
            #     return BurningManAccountingStore.from_proto(proto.burning_man_accounting_store)
            case _:
                raise ProtobufferException("Unknown proto message case(PB.PersistableEnvelope). "
                                           f"messageCase={proto.WhichOneof('message')}; proto raw data={str(proto)}")