from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.config.config import Config
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.exceptions.publish_to_p2p_network_exception import (
    PublishToP2PNetworkException,
)
from bisq.core.dao.governance.blindvote.blind_vote_consensus import BlindVoteConsensus
from bisq.core.dao.governance.blindvote.storage.blind_vote_payload import (
    BlindVotePayload,
)
from bisq.core.dao.governance.blindvote.vote_with_proposal_tx_id import (
    VoteWithProposalTxId,
)
from bisq.core.dao.governance.blindvote.vote_with_proposal_tx_id_list import (
    VoteWithProposalTxIdList,
)
from bisq.core.dao.governance.merit.merit_consensus import MeritConsensus
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.blindvote.my_blind_vote_list import MyBlindVoteList
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.ballot_list import BallotList
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from bisq.core.dao.state.model.governance.merit import Merit
from bisq.core.dao.state.model.governance.merit_list import MeritList
from bitcoinj.base.coin import Coin
from utils.data import SimplePropertyChangeEvent
from utils.preconditions import check_argument
from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
from utils.time import get_time_ms


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.governance.ballot.ballot_list_service import BallotListService
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.proposal.my_proposal_list_service import (
        MyProposalListService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.dao.governance.myvote.my_vote_list_service import MyVoteListService

logger = get_logger(__name__)


class MyBlindVoteListService(PersistedDataHost, DaoStateListener, DaoSetupService):
    """
    Publishes blind vote tx and blind vote payload to p2p network.
    Maintains myBlindVoteList for own blind votes. Triggers republishing of my blind votes at startup during blind
    vote phase of current cycle.
    Publishes a BlindVote and the blind vote transaction.
    """

    def __init__(
        self,
        p2p_service: "P2PService",
        dao_state_service: "DaoStateService",
        period_service: "PeriodService",
        wallets_manager: "WalletsManager",
        persistence_manager: "PersistenceManager[MyBlindVoteList]",
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        ballot_list_service: "BallotListService",
        my_vote_list_service: "MyVoteListService",
        my_proposal_list_service: "MyProposalListService",
    ):
        self.p2p_service = p2p_service
        self.dao_state_service = dao_state_service
        self.period_service = period_service
        self.wallets_manager = wallets_manager
        self.persistence_manager = persistence_manager
        self.bsq_wallet_service = bsq_wallet_service
        self.btc_wallet_service = btc_wallet_service
        self.ballot_list_service = ballot_list_service
        self.my_vote_list_service = my_vote_list_service
        self.my_proposal_list_service = my_proposal_list_service

        self.my_blind_vote_list = MyBlindVoteList()

        self.persistence_manager.initialize(
            self.my_blind_vote_list, PersistenceManagerSource.PRIVATE
        )

    def _num_connected_peers_listener(self, e: SimplePropertyChangeEvent[int]):
        self._maybe_republish_my_blind_vote()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self.dao_state_service.add_dao_state_listener(self)
        self.p2p_service.num_connected_peers_property.add_listener(
            self._num_connected_peers_listener
        )

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        def on_persisted_read(persisted: "MyBlindVoteList"):
            self.my_blind_vote_list.set_all(persisted.list)
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted_read, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_chain_complete(self):
        self._maybe_republish_my_blind_vote()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_mining_fee_and_tx_vsize(self, stake: Coin) -> tuple[Coin, int]:
        # We set dummy opReturn data
        blind_vote_fee = BlindVoteConsensus.get_fee(
            self.dao_state_service, self.dao_state_service.chain_height
        )
        dummy_tx = self._get_blind_vote_tx(stake, blind_vote_fee, bytes(22))
        mining_fee = dummy_tx.get_fee()
        tx_vsize = dummy_tx.get_vsize()
        return mining_fee, tx_vsize

    def publish_blind_vote(
        self,
        stake: Coin,
        result_handler: Callable[[], None],
        exception_handler: Callable[[Exception], None],
    ):
        try:
            secret_key = BlindVoteConsensus.create_secret_key()
            sorted_ballot_list = BlindVoteConsensus.get_sorted_ballot_list(
                self.ballot_list_service
            )
            encrypted_votes = self._get_encrypted_votes(sorted_ballot_list, secret_key)
            op_return_data = self._get_op_return_data(encrypted_votes)
            blind_vote_fee = BlindVoteConsensus.get_fee(
                self.dao_state_service, self.dao_state_service.chain_height
            )
            blind_vote_tx = self._get_blind_vote_tx(
                stake, blind_vote_fee, op_return_data
            )
            blind_vote_tx_id = blind_vote_tx.get_tx_id()

            encrypted_merit_list = self._get_encrypted_merit_list(
                blind_vote_tx_id, secret_key
            )

            # We prefer to not wait for the tx broadcast as if the tx broadcast would fail we still prefer to have our
            # blind vote stored and broadcasted to the p2p network. The tx might get re-broadcasted at a restart and
            # in worst case if it does not succeed the blind vote will be ignored anyway.
            # Inconsistently propagated blind votes in the p2p network could have potentially worse effects.
            blind_vote = BlindVote(
                encrypted_votes,
                blind_vote_tx_id,
                stake.value,
                encrypted_merit_list,
                get_time_ms(),
                {},
            )
            self._add_blind_vote_to_list(blind_vote)

            self._add_to_p2p_network(
                blind_vote,
                lambda error_message: (
                    logger.error(error_message),
                    exception_handler(PublishToP2PNetworkException(error_message)),
                ),
            )

            # We store our source data for the blind vote in myVoteList
            self.my_vote_list_service.create_and_add_my_vote(
                sorted_ballot_list, secret_key, blind_vote
            )

            self._publish_tx(result_handler, exception_handler, blind_vote_tx)
        except Exception as e:
            logger.error(str(e), exc_info=e)
            exception_handler(e)

    def get_currently_available_merit(self) -> int:
        merit_list = self.get_merits(None)
        return MeritConsensus.get_currently_available_merit(
            merit_list, self.dao_state_service.chain_height
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_encrypted_votes(
        self, sorted_ballot_list: BallotList, secret_key: bytes
    ) -> bytes:
        # We don't want to store the proposal but only use the proposalTxId as reference in our encrypted list.
        # So we convert it to the VoteWithProposalTxIdList.
        # The VoteWithProposalTxIdList is used for serialization with protobuf, it is not actually persisted but we
        # use the PersistableList base class for convenience.
        vote_with_proposal_tx_id_list = [
            VoteWithProposalTxId(ballot.tx_id, ballot.vote)
            for ballot in sorted_ballot_list
        ]
        vote_with_proposal_tx_id_list_obj = VoteWithProposalTxIdList(
            vote_with_proposal_tx_id_list
        )
        logger.info(
            f"voteWithProposalTxIdList used in blind vote. voteWithProposalTxIdList={vote_with_proposal_tx_id_list_obj}"
        )
        return BlindVoteConsensus.get_encrypted_votes(
            vote_with_proposal_tx_id_list_obj, secret_key
        )

    def _get_op_return_data(self, encrypted_votes: bytes) -> bytes:
        # We cannot use hash of whole blindVote data because we create the merit signature with the blindVoteTxId
        # So we use the encryptedVotes for the hash only.
        hash = BlindVoteConsensus.get_hash_of_encrypted_votes(encrypted_votes)
        logger.info(
            f"Sha256Ripemd160 hash of encryptedVotes: {bytes_as_hex_string(hash)}"
        )
        return BlindVoteConsensus.get_op_return_data(hash)

    def _get_encrypted_merit_list(
        self, blind_vote_tx_id: Optional[str], secret_key: bytes
    ) -> bytes:
        merit_list = self.get_merits(blind_vote_tx_id)
        return BlindVoteConsensus.get_encrypted_merit_list(merit_list, secret_key)

    # blindVoteTxId is null if we use the method from the getCurrentlyAvailableMerit call.
    def get_merits(self, blind_vote_tx_id: Optional[str]) -> MeritList:
        # Create a lookup set for txIds of own comp. requests from past cycles (we ignore request form that cycle)
        my_compensation_proposal_tx_ids = {
            proposal.tx_id
            for proposal in self.my_proposal_list_service.list
            if isinstance(proposal, CompensationProposal)
            and self.period_service.is_tx_in_past_cycle(
                proposal.tx_id, self.period_service.chain_height
            )
        }

        merits = []
        for issuance in self.dao_state_service.get_issuance_set_for_type(
            IssuanceType.COMPENSATION
        ):
            check_argument(
                issuance.issuance_type == IssuanceType.COMPENSATION,
                "IssuanceType must be COMPENSATION for MeritList",
            )

            # We check if it is our proposal
            if issuance.tx_id not in my_compensation_proposal_tx_ids:
                continue

            if blind_vote_tx_id:
                pub_key = issuance.pub_key
                if not pub_key:
                    logger.error(
                        f"We did not have a pubKey in our issuance object. txId={issuance.tx_id}, issuance={issuance}"
                    )
                    continue
                # TODO: recheck after wallet and DeterministicKey implementation
                key = self.bsq_wallet_service.find_key_from_pub_key(
                    bytes.fromhex(pub_key)
                )
                if not key:
                    logger.error(
                        f"We did not find the key for our compensation request. txId={issuance.tx_id}"
                    )
                    continue

                # We sign the txId so we be sure that the signature could not be used by anyone else
                # In the verification the txId will be checked as well.

                # Java Implementation uses BitcoinJ EC keys
                # We need to use a compatible way to sign the txId
                signature = (
                    key.sign(bytes.fromhex(blind_vote_tx_id))
                    if not self.bsq_wallet_service.is_encrypted
                    else key.sign(
                        bytes.fromhex(blind_vote_tx_id), self.bsq_wallet_service.password
                    )
                )
                signature_as_bytes = signature.to_canonicalised().encode_to_der()
            else:
                # In case we use it for requesting the currently available merit we don't apply a signature
                signature_as_bytes = b""

            merits.append(Merit(issuance, signature_as_bytes))

        return MeritList(sorted(merits, key=lambda merit: merit.issuance.tx_id))

    def _publish_tx(
        self,
        result_handler: Callable[[], None],
        exception_handler: Callable[[Exception], None],
        blind_vote_tx: "Transaction",
    ):
        logger.info(f"blindVoteTx={blind_vote_tx}")

        class Listener(TxBroadcasterCallback):
            def on_success(self, transaction: "Transaction"):
                logger.info(f"BlindVote tx published. txId={transaction.get_tx_id()}")
                result_handler()

            def on_failure(self, exception: Exception):
                exception_handler(exception)

        self.wallets_manager.publish_and_commit_bsq_tx(
            blind_vote_tx,
            TxType.BLIND_VOTE,
            Listener(),
        )

    def _get_blind_vote_tx(
        self, stake: Coin, fee: Coin, op_return_data: bytes
    ) -> "Transaction":
        # TODO
        prepared_tx = self.bsq_wallet_service.get_prepared_blind_vote_tx(fee, stake)
        tx_with_btc_fee = self.btc_wallet_service.complete_prepared_blind_vote_tx(
            prepared_tx, op_return_data
        )
        return self.bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
            tx_with_btc_fee
        )

    def _maybe_republish_my_blind_vote(self):
        # We do not republish during vote reveal phase as peer would reject blindVote data to protect against
        # late publishing attacks.
        # This attack is only relevant during the vote reveal phase as there it could cause damage by disturbing the
        # data view of the blind votes of the voter for creating the majority hash.
        # To republish after the vote reveal phase still makes sense to reduce risk that some nodes have not received
        # it and would need to request the data then in the vote result phase.
        if not self.period_service.is_in_phase(
            self.dao_state_service.chain_height, DaoPhase.Phase.VOTE_REVEAL
        ):
            # We republish at each startup at any block during the cycle. We filter anyway for valid blind votes
            # of that cycle so it is 1 blind vote getting rebroadcast at each startup to my neighbors.
            # Republishing only will have effect if the payload creation date is < 5 hours as other nodes would not
            # accept payloads which are too old or are in future.
            # Only payloads received from seed nodes would ignore that date check.
            min_peers = 4 if Config.BASE_CURRENCY_NETWORK_VALUE.is_mainnet() else 1
            if (
                self.p2p_service.num_connected_peers >= min_peers
                and self.p2p_service.is_bootstrapped
            ) or Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest():
                for blind_vote in self.my_blind_vote_list:
                    if self.period_service.is_tx_in_phase_and_cycle(
                        blind_vote.tx_id,
                        DaoPhase.Phase.BLIND_VOTE,
                        self.period_service.chain_height,
                    ):
                        self._add_to_p2p_network(blind_vote, None)

                # We delay removal of listener as we call that inside listener itself.
                UserThread.execute(
                    lambda: self.p2p_service.num_connected_peers_property.remove_listener(
                        self._num_connected_peers_listener
                    )
                )

    def _add_to_p2p_network(
        self, blind_vote: "BlindVote", error_message_handler: ErrorMessageHandler = None
    ):
        blind_vote_payload = BlindVotePayload(blind_vote)
        # We use reBroadcast flag here as we only broadcast our own blindVote and want to be sure it gets distributed well.
        success = self.p2p_service.add_persistable_network_payload(
            blind_vote_payload, True
        )

        if success:
            logger.info(
                f"We added a blindVotePayload to the P2P network as append only data. blindVoteTxId={blind_vote.tx_id}"
            )
        else:
            msg = f"Adding of blindVotePayload to P2P network failed. blindVoteTxId={blind_vote.tx_id}"
            logger.error(msg)
            if error_message_handler:
                error_message_handler(msg)

    def _add_blind_vote_to_list(self, blind_vote: "BlindVote"):
        if blind_vote not in self.my_blind_vote_list.list:
            self.my_blind_vote_list.append(blind_vote)
            self._request_persistence()

    def _request_persistence(self):
        self.persistence_manager.request_persistence()
