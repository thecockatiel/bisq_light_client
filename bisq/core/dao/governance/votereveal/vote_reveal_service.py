from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.blindvote.blind_vote_consensus import BlindVoteConsensus
from bisq.core.dao.governance.votereveal.vote_reveal_consensus import (
    VoteRevealConsensus,
)
from bisq.core.dao.governance.votereveal.vote_reveal_exception import (
    VoteRevealException,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from utils.data import ObservableChangeEvent, ObservableList
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.state.model.blockchain.tx_type import TxType

if TYPE_CHECKING:
    from bisq.core.dao.governance.myvote.my_vote import MyVote
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bitcoinj.core.transaction import Transaction
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.governance.votereveal.vote_reveal_tx_published_listener import (
        VoteRevealTxPublishedListener,
    )
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
        BlindVoteListService,
    )
    from bisq.core.dao.governance.myvote.my_vote_list_service import MyVoteListService
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService


# JAVA TODO Broadcast the winning list at the moment the reveal period is over and have the break
# interval as time buffer for all nodes to receive that winning list. All nodes which are in sync with the
# majority data view can broadcast. That way it will become a very unlikely case that a node is missing
# data.


class VoteRevealService(DaoStateListener, DaoSetupService):
    """
    Publishes voteRevealTx with the secret key used for encryption at blind vote and the hash of the list of
    the blind vote payloads. Republishes also all blindVotes of that cycle to add more resilience.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        blind_vote_list_service: "BlindVoteListService",
        period_service: "PeriodService",
        my_vote_list_service: "MyVoteListService",
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        wallets_manager: "WalletsManager",
    ):
        self.logger = get_ctx_logger(__name__)
        self._dao_state_service = dao_state_service
        self._blind_vote_list_service = blind_vote_list_service
        self._period_service = period_service
        self._my_vote_list_service = my_vote_list_service
        self._bsq_wallet_service = bsq_wallet_service
        self._btc_wallet_service = btc_wallet_service
        self._wallets_manager = wallets_manager

        self.vote_reveal_exceptions = ObservableList["VoteRevealException"]()
        self._vote_reveal_tx_published_listeners: set[
            "VoteRevealTxPublishedListener"
        ] = set()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self.vote_reveal_exceptions.add_listener(self._on_exceptions_changed)
        self._dao_state_service.add_dao_state_listener(self)

    def _on_exceptions_changed(self, e: ObservableChangeEvent["VoteRevealException"]):
        if e.added_elements:
            for exception in e.added_elements:
                self.logger.error(str(exception))

    def start(self):
        pass

    def shut_down(self):
        self.vote_reveal_exceptions.remove_listener(self._on_exceptions_changed)
        self._dao_state_service.remove_dao_state_listener(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_hash_of_blind_vote_list(self) -> bytes:
        blind_votes = BlindVoteConsensus.get_sorted_blind_vote_list_of_cycle(
            self._blind_vote_list_service
        )
        hash_of_blind_vote_list = VoteRevealConsensus.get_hash_of_blind_vote_list(
            blind_votes
        )
        self.logger.debug(f"blindVoteList for creating hash: {blind_votes}")
        self.logger.info(
            f"Sha256Ripemd160 hash of hashOfBlindVoteList {bytes_as_hex_string(hash_of_blind_vote_list)}"
        )
        return hash_of_blind_vote_list

    def add_vote_reveal_tx_published_listener(
        self, vote_reveal_tx_published_listener: "VoteRevealTxPublishedListener"
    ):
        self._vote_reveal_tx_published_listeners.add(vote_reveal_tx_published_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self._maybe_reveal_votes(block.height)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Creation of vote reveal tx is done without user activity!
    # We create automatically the vote reveal tx when we are in the reveal phase of the current cycle when
    # the blind vote was created in case we have not done it already.
    # The voter needs to be at least once online in the reveal phase when he has a blind vote created,
    # otherwise his vote becomes invalid.
    # In case the user misses the vote reveal phase an (invalid) vote reveal tx will be created the next time the user is
    # online. That tx only serves the purpose to unlock the stake from the blind vote but it will be ignored for voting.
    # A blind vote which did not get revealed might still be part of the majority hash calculation as we cannot know
    # which blind votes might be revealed until the phase is over at the moment when we publish the vote reveal tx.
    def _maybe_reveal_votes(self, chain_height: int):
        for my_vote in self._my_vote_list_service.my_vote_list:
            if my_vote.reveal_tx_id is None:  # we have not already revealed
                is_in_vote_reveal_phase = (
                    self._period_service.get_phase_for_height(chain_height)
                    == DaoPhase.Phase.VOTE_REVEAL
                )
                # If we would create the tx in the last block it would be confirmed in the best case in the next
                # block which would be already the break and would invalidate the vote reveal.
                is_last_block_in_phase = (
                    chain_height
                    == self._period_service.get_last_block_of_phase(
                        chain_height, DaoPhase.Phase.VOTE_REVEAL
                    )
                )
                blind_vote_tx_id = my_vote.blind_vote_tx_id
                is_blind_vote_tx_in_correct_phase_and_cycle = (
                    self._period_service.is_tx_in_phase_and_cycle(
                        blind_vote_tx_id, DaoPhase.Phase.BLIND_VOTE, chain_height
                    )
                )
                if (
                    is_in_vote_reveal_phase
                    and not is_last_block_in_phase
                    and is_blind_vote_tx_in_correct_phase_and_cycle
                ):
                    self.logger.info(
                        f"We call revealVote at blockHeight {chain_height} for blindVoteTxId {blind_vote_tx_id}"
                    )
                    # Standard case that we are in the correct phase and cycle and create the reveal tx.
                    self._reveal_vote(my_vote, True)
                else:
                    # We missed the vote reveal phase but publish a vote reveal tx to unlock the blind vote stake.
                    is_after_vote_reveal_phase = (
                        self._period_service.get_phase_for_height(chain_height).value
                        > DaoPhase.Phase.VOTE_REVEAL.value
                    )

                    # We missed the reveal phase but we are in the correct cycle
                    missed_phase_same_cycle = (
                        is_after_vote_reveal_phase
                        and is_blind_vote_tx_in_correct_phase_and_cycle
                    )

                    # If we missed the cycle we don't care about the phase anymore.
                    is_blind_vote_tx_in_past_cycle = (
                        self._period_service.is_tx_in_past_cycle(
                            blind_vote_tx_id, chain_height
                        )
                    )
                    if missed_phase_same_cycle or is_blind_vote_tx_in_past_cycle:
                        # Exceptional case that the user missed the vote reveal phase. We still publish the vote
                        # reveal tx to unlock the vote stake.

                        # We cannot handle that case in the parser directly to avoid that reveal tx and unlock the
                        # BSQ because the blind vote tx is already in the snapshot and does not get parsed
                        # again. It would require a reset of the snapshot and parse all blocks again.
                        # As this is an exceptional case we prefer to have a simple solution instead and just
                        # publish the vote reveal tx but are aware that it is invalid.
                        self.logger.warning(
                            f"We missed the vote reveal phase but publish now the tx to unlock our locked BSQ from the blind vote tx. BlindVoteTxId={blind_vote_tx_id}, blockHeight={chain_height}"
                        )
                        # We handle the exception here inside the stream iteration as we have not get triggered from an
                        # outside user intent anyway. We keep errors in a observable list so clients can observe that to
                        # get notified if anything went wrong.
                        self._reveal_vote(my_vote, False)

    def _reveal_vote(self, my_vote: "MyVote", is_in_vote_reveal_phase: bool):
        try:
            # We collect all valid blind vote items we received via the p2p network.
            # It might be that different nodes have a different collection of those items.
            # To ensure we get a consensus of the data for later calculating the result we will put a hash of each
            # voter's blind vote collection into the opReturn data and check for a majority in the vote result phase.
            # The voters "vote" with their stake at the reveal tx for their version of the blind vote collection.

            # If we are not in the right phase we just add an empty hash (still need to have the hash as otherwise we
            # would not recognize the tx as vote reveal tx)
            hash_of_blind_vote_list = (
                self._get_hash_of_blind_vote_list()
                if is_in_vote_reveal_phase
                else bytes(20)
            )
            op_return_data = VoteRevealConsensus.get_op_return_data(
                hash_of_blind_vote_list,
                my_vote.secret_key_encoded,
            )

            # We search for my unspent stake output.
            # my_vote is already tested if it is in current cycle at maybe_reveal_votes
            # We expect that the blind vote tx and stake output is available. If not we throw an exception.
            stake_tx_output = next(
                (
                    tx_output
                    for tx_output in self._dao_state_service.get_unspent_blind_vote_stake_tx_outputs()
                    if tx_output.tx_id == my_vote.blind_vote_tx_id
                ),
                None,
            )
            if not stake_tx_output:
                raise VoteRevealException(
                    "stakeTxOutput is not found for myVote.", my_vote=my_vote
                )

            vote_reveal_tx = self._get_vote_reveal_tx(stake_tx_output, op_return_data)
            self.logger.info(f"voteRevealTx={vote_reveal_tx}")
            self._publish_tx(vote_reveal_tx)

            # We don't want to wait for a successful broadcast to avoid issues if the broadcast succeeds delayed or at
            # next startup but the tx was actually broadcast.
            self._my_vote_list_service.apply_reveal_tx_id(
                my_vote, vote_reveal_tx.get_tx_id()
            )
        except VoteRevealException as e:
            self.vote_reveal_exceptions.append(e)
        except Exception as e:
            self.vote_reveal_exceptions.append(
                VoteRevealException(
                    "Exception at calling revealVote.",
                    e,
                    blind_vote_tx_id=my_vote.blind_vote_tx_id,
                )
            )

    def _publish_tx(self, vote_reveal_tx: "Transaction"):
        class Callback(TxBroadcasterCallback):
            def on_success(self_, transaction: "Transaction"):
                self.logger.info("voteRevealTx successfully broadcast.")
                for listener in self._vote_reveal_tx_published_listeners:
                    listener(transaction.get_tx_id())

            def on_failure(self_, exception: Exception):
                self.logger.error(str(exception))
                self.vote_reveal_exceptions.append(
                    VoteRevealException(
                        "Publishing of voteRevealTx failed.",
                        exception,
                        vote_reveal_tx=vote_reveal_tx,
                    )
                )

        self._wallets_manager.publish_and_commit_bsq_tx(
            vote_reveal_tx,
            TxType.VOTE_REVEAL,
            Callback(),
        )

    def _get_vote_reveal_tx(
        self, stake_tx_output: "TxOutput", op_return_data: bytes
    ) -> "Transaction":
        prepared_tx = self._bsq_wallet_service.get_prepared_vote_reveal_tx(
            stake_tx_output
        )
        tx_with_btc_fee = self._btc_wallet_service.complete_prepared_vote_reveal_tx(
            prepared_tx, op_return_data
        )
        return self._bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
            tx_with_btc_fee
        )
