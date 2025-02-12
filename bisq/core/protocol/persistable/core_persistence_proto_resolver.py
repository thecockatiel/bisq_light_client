from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.navigation_path import NavigationPath
from bisq.common.protocol.persistable.persistence_proto_resolver import PersistenceProtoResolver
from bisq.common.setup.log_setup import get_logger
from bisq.core.account.sign.signed_witness_store import SignedWitnessStore
from bisq.core.account.witness.account_age_witness_store import AccountAgeWitnessStore
from bisq.core.btc.model.address_entry_list import AddressEntryList
from bisq.core.dao.burningman.accounting.storage.burning_man_accounting_store import BurningManAccountingStore
from bisq.core.dao.governance.blindvote.my_blind_vote_list import MyBlindVoteList
from bisq.core.dao.governance.bond.reputation.my_reputation_list import MyReputationList
from bisq.core.dao.governance.proofofburn.my_proof_of_burn_list import MyProofOfBurnList
from bisq.core.dao.state.storage.bsq_block_store import BsqBlockStore
from bisq.core.dao.state.storage.dao_state_store import DaoStateStore
from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list import UnconfirmedBsqChangeOutputList
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
from bisq.core.trade.model.tradable_list import TradableList
from bisq.core.user.preferences_payload import PreferencesPayload
from bisq.core.user.user_payload import UserPayload
import pb_pb2 as protobuf
from utils.di import DependencyProvider

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from utils.clock import Clock

logger = get_logger(__name__)

proto_map: dict[str, Callable[[protobuf.PersistableEnvelope, "CorePersistenceProtoResolver"], "PersistableEnvelope"]] = {
    "sequence_number_map": lambda p, resolver: SequenceNumberMap.from_proto(p.sequence_number_map),
    "peer_list": lambda p, resolver: PeerList.from_proto(p.peer_list),
    "address_entry_list": lambda p, resolver: AddressEntryList.from_proto(p.address_entry_list),
    "tradable_list": lambda p, resolver: TradableList.from_proto(p.tradable_list, resolver, resolver.btc_wallet_service_provider.get()),
    "arbitration_dispute_list": lambda p, resolver: ArbitrationDisputeList.from_proto(p.arbitration_dispute_list, resolver),
    "mediation_dispute_list": lambda p, resolver: MediationDisputeList.from_proto(p.mediation_dispute_list, resolver),
    "refund_dispute_list": lambda p, resolver: RefundDisputeList.from_proto(p.refund_dispute_list, resolver),
    "preferences_payload": lambda p, resolver: PreferencesPayload.from_proto(p.preferences_payload, resolver),
    "user_payload": lambda p, resolver: UserPayload.from_proto(p.user_payload, resolver),
    "navigation_path": lambda p, resolver: NavigationPath.from_proto(p.navigation_path),
    "payment_account_list": lambda p, resolver: PaymentAccountList.from_proto(p.payment_account_list, resolver),
    "account_age_witness_store": lambda p, resolver: AccountAgeWitnessStore.from_proto(p.account_age_witness_store),
    # "trade_statistics2_store": lambda p, resolver: TradeStatistics2Store.from_proto(p),
    # "blind_vote_store": lambda p, resolver: BlindVoteStore.from_proto(p),
    # "proposal_store": lambda p, resolver: ProposalStore.from_proto(p),
    # "temp_proposal_store": lambda p, resolver: TempProposalStore.from_proto(p, resolver.network_proto_resolver),
    # "my_proposal_list": lambda p, resolver: MyProposalList.from_proto(p),
    # "ballot_list": lambda p, resolver: BallotList.from_proto(p),
    # "my_vote_list": lambda p, resolver: MyVoteList.from_proto(p),
    "my_blind_vote_list": lambda p, resolver: MyBlindVoteList.from_proto(p.my_blind_vote_list),
    "dao_state_store": lambda p, resolver: DaoStateStore.from_proto(p.dao_state_store),
    "my_reputation_list": lambda p, resolver: MyReputationList.from_proto(p.my_reputation_list),
    "my_proof_of_burn_list": lambda p, resolver: MyProofOfBurnList.from_proto(p.my_proof_of_burn_list),
    "unconfirmed_bsq_change_output_list": lambda p, resolver: UnconfirmedBsqChangeOutputList.from_proto(p.unconfirmed_bsq_change_output_list),
    "signed_witness_store": lambda p, resolver: SignedWitnessStore.from_proto(p.signed_witness_store),
    # "trade_statistics3_store": lambda p, resolver: TradeStatistics3Store.from_proto(p),
    "mailbox_message_list": lambda p, resolver: MailboxMessageList.from_proto(p.mailbox_message_list, resolver.network_proto_resolver),
    "ignored_mailbox_map": lambda p, resolver: IgnoredMailboxMap.from_proto(p.ignored_mailbox_map),
    "removed_payloads_map": lambda p, resolver: RemovedPayloadsMap.from_proto(p.removed_payloads_map),
    "bsq_block_store": lambda p, resolver: BsqBlockStore.from_proto(p.bsq_block_store),
    "burning_man_accounting_store": lambda p, resolver: BurningManAccountingStore.from_proto(p.burning_man_accounting_store),
}

class CorePersistenceProtoResolver(CoreProtoResolver, PersistenceProtoResolver):
    def __init__(self, clock: "Clock", btc_wallet_service_provider: DependencyProvider["BtcWalletService"], network_proto_resolver: "NetworkProtoResolver"):
        super().__init__(clock)
        self.btc_wallet_service_provider = btc_wallet_service_provider
        self.network_proto_resolver = network_proto_resolver
        
    def from_proto(self, proto: protobuf.PersistableEnvelope) -> "PersistableEnvelope":
        if proto is None:
            logger.error("PersistableEnvelope.from_proto: PB.PersistableEnvelope is null")
            raise ProtobufferException("PB.PersistableEnvelope is null")
        
        message_type = proto.WhichOneof("message")
        if message_type in proto_map:
            return proto_map[message_type](proto, self)
        else:
            raise ProtobufferException("Unknown proto message case(PB.PersistableEnvelope). "
                                       f"messageCase={message_type}; proto raw data={str(proto)}")
