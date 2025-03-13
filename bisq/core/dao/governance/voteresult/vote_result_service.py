from dataclasses import dataclass
import traceback
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.common.util.permutation_util import PermutationUtil
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.blindvote.blind_vote_consensus import BlindVoteConsensus
from bisq.core.dao.governance.merit.merit_consensus import MeritConsensus
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.issuance_proposal import IssuanceProposal
from bisq.core.dao.governance.voteresult.missing_data_request_service import (
    MissingDataRequestService,
)
from bisq.core.dao.governance.voteresult.vote_result_consensus import (
    VoteResultConsensus,
)
from bisq.core.dao.governance.votereveal.vote_reveal_consensus import (
    VoteRevealConsensus,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.ballot import Ballot
from bisq.core.dao.state.model.governance.ballot_list import BallotList
from bisq.core.dao.state.model.governance.change_param_proposal import (
    ChangeParamProposal,
)
from bisq.core.dao.state.model.governance.confiscate_bond_proposal import (
    ConfiscateBondProposal,
)
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.governance.merit_list import MeritList
from bisq.core.dao.state.model.governance.param_change import ParamChange
from bisq.core.dao.state.model.governance.proposal_vote_result import ProposalVoteResult
from bisq.core.dao.state.model.governance.remove_asset_proposal import (
    RemoveAssetProposal,
)
from bisq.core.dao.state.model.governance.role_proposal import RoleProposal
from bisq.core.dao.state.model.governance.vote import Vote
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from utils.data import ObservableList
from bisq.core.dao.governance.voteresult.vote_result_exception import (
    VoteResultException,
)
from utils.preconditions import check_argument
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.state.model.governance.cycle import Cycle
    from bisq.core.dao.governance.blindvote.vote_with_proposal_tx_id_list import (
        VoteWithProposalTxIdList,
    )
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bisq.core.dao.state.model.governance.evaluated_proposal import (
        EvaluatedProposal,
    )
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.governance.voteresult.issuance.issuance_service import (
        IssuanceService,
    )
    from bisq.core.dao.governance.proposal.proposal_list_presentation import (
        ProposalListPresentation,
    )
    from bisq.core.dao.state.model.governance.decrypted_ballots_with_merits import (
        DecryptedBallotsWithMerits,
    )
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
        BlindVoteListService,
    )
    from bisq.core.dao.governance.ballot.ballot_list_service import BallotListService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.governance.blindvote.blind_vote import BlindVote


logger = get_logger(__name__)


class VoteResultService(DaoStateListener, DaoSetupService):
    """
    Calculates the result of the voting at the VoteResult period.
    We take all data from the bitcoin domain and additionally the blindVote list which we received from the p2p network.
    Due to eventual consistency we use the hash of the data view of the voters (majority by merit+stake). If our local
    blindVote list contains the blindVotes used by the voters we can calculate the result, otherwise we need to request
    the missing blindVotes from the network.
    """

    def __init__(
        self,
        proposal_list_presentation: "ProposalListPresentation",
        dao_state_service: "DaoStateService",
        period_service: "PeriodService",
        ballot_list_service: "BallotListService",
        blind_vote_list_service: "BlindVoteListService",
        issuance_service: "IssuanceService",
        missing_data_request_service: "MissingDataRequestService",
    ):
        self._proposal_list_presentation = proposal_list_presentation
        self._dao_state_service = dao_state_service
        self._period_service = period_service
        self._ballot_list_service = ballot_list_service
        self._blind_vote_list_service = blind_vote_list_service
        self._issuance_service = issuance_service
        self._missing_data_request_service = missing_data_request_service
        self.vote_result_exceptions = ObservableList["VoteResultException"]()
        self.invalid_decrypted_ballots_with_merit_items = set[
            "DecryptedBallotsWithMerits"
        ]()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._dao_state_service.add_dao_state_listener(self)

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete(self, block: "Block"):
        self._maybe_calculate_vote_result(block.height)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _maybe_calculate_vote_result(self, chain_height: int):
        if self._is_in_vote_result_phase(chain_height):
            logger.info(f"CalculateVoteResult at chainHeight={chain_height}")
            current_cycle = self._period_service.current_cycle
            assert current_cycle is not None, "current_cycle must not be None"
            start_ts = get_time_ms()

            decrypted_ballots_with_merits_set = (
                self._get_decrypted_ballots_with_merits_set(chain_height)
            )
            if decrypted_ballots_with_merits_set:
                # From the decryptedBallotsWithMeritsSet we create a map with the hash of the blind vote list as key and the
                # aggregated stake as value (no merit as that is part of the P2P network data and might lead to inconsistency).
                # That map is used for calculating the majority of the blind vote lists.
                # There might be conflicting versions due the eventually consistency of the P2P network (if some blind
                # vote payloads do not arrive at all voters) which would lead to consensus failure in the result calculation.
                # To solve that problem we will only consider the blind votes valid which are matching the majority hash.
                # If multiple data views would have the same stake we sort additionally by the hex value of the
                # blind vote hash and use the first one in the sorted list as winner.
                # A node which has a local blindVote list which does not match the winner data view will try
                # permutations of his local list and if that does not succeed he need to recover it's
                # local blindVote list by requesting the correct list from other peers.
                stakes = self._get_stake_by_hash_of_blind_vote_list_map(
                    decrypted_ballots_with_merits_set
                )

                try:
                    # Get majority hash
                    majority_blind_vote_list_hash = (
                        self._calculate_majority_blind_vote_list_hash(stakes)
                    )

                    # Is our local list matching the majority data view?
                    blind_vote_list = self._find_blind_vote_list_matching_majority_hash(
                        majority_blind_vote_list_hash
                    )
                    if blind_vote_list:
                        logger.debug(
                            "blindVoteListMatchingMajorityHash: {}".format(
                                str(
                                    [
                                        f"blindVoteTxId={vote.tx_id}, Stake={vote.stake}"
                                        for vote in blind_vote_list
                                    ]
                                )
                            ),
                        )

                        blind_vote_tx_id_set = {vote.tx_id for vote in blind_vote_list}
                        # We need to filter out result list according to the majority hash list
                        filtered_decrypted_ballots_with_merits_set = set[
                            "DecryptedBallotsWithMerits"
                        ]()
                        for ballots in decrypted_ballots_with_merits_set:
                            if ballots.blind_vote_tx_id in blind_vote_tx_id_set:
                                filtered_decrypted_ballots_with_merits_set.add(ballots)
                            else:
                                self.invalid_decrypted_ballots_with_merit_items.add(
                                    ballots
                                )

                        # Only if we have all blind vote payloads and know the right list matching the majority we add
                        # it to our state. Otherwise we are not in consensus with the network.
                        self._dao_state_service.add_decrypted_ballots_with_merits_set(
                            filtered_decrypted_ballots_with_merits_set
                        )

                        evaluated_proposals = self._get_evaluated_proposals(
                            filtered_decrypted_ballots_with_merits_set, chain_height
                        )
                        self._dao_state_service.add_evaluated_proposal_set(
                            evaluated_proposals
                        )
                        accepted_evaluated_proposals = (
                            self._get_accepted_evaluated_proposals(evaluated_proposals)
                        )
                        self._apply_accepted_proposals(
                            accepted_evaluated_proposals, chain_height
                        )
                        logger.info("processAllVoteResults completed")
                    else:
                        msg = "We could not find a list which matches the majority so we cannot calculate the vote result. Please restart and resync the DAO state."
                        logger.warning(msg)
                        self.vote_result_exceptions.append(
                            VoteResultException(current_cycle, Exception(msg))
                        )

                except Exception as e:
                    logger.warning(str(e))
                    logger.warning(
                        f"decryptedBallotsWithMeritsSet {decrypted_ballots_with_merits_set}"
                    )
                    traceback.print_exc()
                    self.vote_result_exceptions.append(
                        VoteResultException(current_cycle, e)
                    )
            else:
                logger.info(
                    f"There have not been any votes in that cycle. chainHeight={chain_height}"
                )

            logger.info(f"Evaluating vote result took {get_time_ms() - start_ts} ms")

    def _get_decrypted_ballots_with_merits_set(
        self, chain_height: int
    ) -> set["DecryptedBallotsWithMerits"]:
        # We want all voteRevealTxOutputs which are in current cycle we are processing
        return {
            result
            for tx_output in self._dao_state_service.get_vote_reveal_op_return_tx_outputs()
            if self._period_service.is_tx_in_correct_cycle_by_id(
                tx_output.tx_id, chain_height
            )
            and self._is_in_vote_reveal_phase(tx_output)
            if (
                result := self._tx_output_to_decrypted_ballots_with_merits(
                    tx_output, chain_height
                )
            )
            is not None
        }

    def _is_in_vote_reveal_phase(self, tx_output: "TxOutput") -> bool:
        vote_reveal_tx = tx_output.tx_id
        tx_in_phase = self._period_service.is_tx_in_phase(
            vote_reveal_tx, DaoPhase.Phase.VOTE_REVEAL
        )
        if not tx_in_phase:
            logger.warning(
                f"We got a vote reveal tx with was not in the correct phase of that cycle. voteRevealTxId={vote_reveal_tx}"
            )

        return tx_in_phase

    def _tx_output_to_decrypted_ballots_with_merits(
        self, vote_reveal_tx_output: "TxOutput", chain_height: int
    ):
        vote_reveal_tx_id = vote_reveal_tx_output.tx_id
        current_cycle = self._period_service.current_cycle
        assert current_cycle is not None, "current_cycle must not be None"
        try:
            vote_reveal_op_return_data = vote_reveal_tx_output.op_return_data
            vote_reveal_tx = self._dao_state_service.get_tx(vote_reveal_tx_id)
            check_argument(
                vote_reveal_tx is not None,
                f"vote_reveal_tx must be present. vote_reveal_tx_id={vote_reveal_tx_id}",
            )

            # Here we use only blockchain tx data so far so we don't have risks with missing P2P network data.
            # We work back from the voteRealTx to the blindVoteTx to calculate the majority hash. From that we
            # will derive the blind vote list we will use for result calculation and as it was based on
            # blockchain data it will be consistent for all peers independent on their P2P network data state.
            blind_vote_stake_output = (
                VoteResultConsensus.get_connected_blind_vote_stake_output(
                    vote_reveal_tx, self._dao_state_service
                )
            )
            blind_vote_tx_id = blind_vote_stake_output.tx_id

            # If we get a blind vote tx which was published too late we ignore it.
            if not self._period_service.is_tx_in_phase_and_cycle(
                blind_vote_tx_id, DaoPhase.Phase.BLIND_VOTE, chain_height
            ):
                logger.warning(
                    f"We got a blind vote tx with was not in the correct phase and/or cycle. "
                    f"We ignore that vote reveal and blind vote tx. vote_reveal_tx={vote_reveal_tx}, blind_vote_tx_id={blind_vote_tx_id}"
                )
                return None

            VoteResultConsensus.validate_blind_vote_tx(
                blind_vote_tx_id,
                self._dao_state_service,
                self._period_service,
                chain_height,
            )

            hash_of_blind_vote_list = VoteResultConsensus.get_hash_of_blind_vote_list(
                vote_reveal_op_return_data
            )
            blind_vote_stake = blind_vote_stake_output.value

            blind_vote_list = BlindVoteConsensus.get_sorted_blind_vote_list_of_cycle(
                self._blind_vote_list_service
            )
            matching_blind_vote = next(
                (bv for bv in blind_vote_list if bv.tx_id == blind_vote_tx_id), None
            )

            if matching_blind_vote is not None:
                return self._get_decrypted_ballots_with_merits(
                    vote_reveal_tx_id,
                    current_cycle,
                    vote_reveal_op_return_data,
                    blind_vote_tx_id,
                    hash_of_blind_vote_list,
                    blind_vote_stake,
                    matching_blind_vote,
                )

            # We are missing P2P network data
            return self._get_empty_decrypted_ballots_with_merits(
                vote_reveal_tx_id,
                blind_vote_tx_id,
                hash_of_blind_vote_list,
                blind_vote_stake,
            )

        except Exception as e:
            logger.error(
                f"Could not create DecryptedBallotsWithMerits from vote_reveal_tx_id {vote_reveal_tx_id} because of "
                f"exception: {str(e)}"
            )
            self.vote_result_exceptions.append(VoteResultException(current_cycle, e))
            return None

    def _get_empty_decrypted_ballots_with_merits(
        self,
        vote_reveal_tx_id: str,
        blind_vote_tx_id: str,
        hash_of_blind_vote_list: bytes,
        blind_vote_stake: int,
    ) -> "DecryptedBallotsWithMerits":
        logger.warning(
            f"We have a blindVoteTx but we do not have the corresponding blindVote payload.\n"
            "That can happen if the blindVote item was not properly broadcast. "
            f"We still add it to our result collection because it might be relevant for the majority "
            f"hash by stake calculation. blindVoteTxId={blind_vote_tx_id}"
        )

        self._missing_data_request_service.send_republish_request()

        # We prefer to use an empty list here instead a null or optional value to avoid that
        # client code need to handle nullable or optional values.
        empty_ballot_list = BallotList([])
        empty_merit_list = MeritList([])

        logger.debug(
            f"Add entry to decrypted_ballots_with_merits_set: blind_vote_tx_id={blind_vote_tx_id}, "
            f"vote_reveal_tx_id={vote_reveal_tx_id}, blind_vote_stake={blind_vote_stake}, "
            f"ballot_list={empty_ballot_list}"
        )

        return DecryptedBallotsWithMerits(
            hash_of_blind_vote_list,
            blind_vote_tx_id,
            vote_reveal_tx_id,
            blind_vote_stake,
            empty_ballot_list,
            empty_merit_list,
        )

    def _get_decrypted_ballots_with_merits(
        self,
        vote_reveal_tx_id: str,
        current_cycle: "Cycle",
        vote_reveal_op_return_data: bytes,
        blind_vote_tx_id: str,
        hash_of_blind_vote_list: bytes,
        blind_vote_stake: int,
        blind_vote: "BlindVote",
    ) -> Optional["DecryptedBallotsWithMerits"]:
        secret_key = VoteResultConsensus.get_secret_key(vote_reveal_op_return_data)
        try:
            vote_with_proposal_tx_id_list = VoteResultConsensus.decrypt_votes(
                blind_vote.encrypted_votes, secret_key
            )
            merit_list = MeritConsensus.decrypt_merit_list(
                blind_vote.encrypted_merit_list, secret_key
            )
            # We lookup for the proposals we have in our local list which match the txId from the
            # voteWithProposalTxIdList and create a ballot list with the proposal and the vote from
            # the voteWithProposalTxIdList
            ballot_list = self._create_ballot_list(vote_with_proposal_tx_id_list)
            logger.debug(
                f"Add entry to decrypted_ballots_with_merits_set: blind_vote_tx_id={blind_vote_tx_id}, "
                f"vote_reveal_tx_id={vote_reveal_tx_id}, blind_vote_stake={blind_vote_stake}, ballot_list={ballot_list}"
            )
            return DecryptedBallotsWithMerits(
                hash_of_blind_vote_list,
                blind_vote_tx_id,
                vote_reveal_tx_id,
                blind_vote_stake,
                ballot_list,
                merit_list,
            )
        except VoteResultException.DecryptionException as decryption_exception:
            # We don't consider such vote reveal txs valid for the majority hash
            # calculation and don't add it to our result collection
            logger.error(
                f"Could not decrypt blind vote. This vote reveal and blind vote will be ignored. "
                f"VoteRevealTxId={vote_reveal_tx_id}. DecryptionException={str(decryption_exception)}"
            )
            self.vote_result_exceptions.append(
                VoteResultException(current_cycle, decryption_exception)
            )
            return None

    def _create_ballot_list(
        self, vote_with_proposal_tx_id_list: "VoteWithProposalTxIdList"
    ) -> BallotList:
        # vote_with_proposal_tx_id_list is the list of ProposalTxId + vote from the blind vote (decrypted vote data)

        # We convert the list to a map with proposalTxId as key and the vote as value.
        vote_by_tx_id_map = {
            vote.proposal_tx_id: vote.vote
            for vote in vote_with_proposal_tx_id_list.list
        }

        # We make a map with proposalTxId as key and the ballot as value out of our stored ballot list.
        # This can contain ballots which have been added later and have a null value for the vote.
        ballot_by_tx_id_map = {
            ballot.tx_id: ballot
            for ballot in self._ballot_list_service.get_valid_ballots_of_cycle()
        }

        # It could be that we missed some proposalPayloads.
        # If we have votes with proposals which are not found in our ballots we add it to missingBallots.
        missing_ballots: list[str] = []
        ballots: list["Ballot"] = []

        # Process votes from blind vote data
        for tx_id, vote in vote_by_tx_id_map.items():
            if tx_id in ballot_by_tx_id_map:
                ballot = ballot_by_tx_id_map[tx_id]
                # We create a new Ballot with the proposal from the ballot list and the vote from our decrypted votes
                # We clone the ballot instead applying the vote to the existing ballot from ballotListService
                # The items from ballotListService.getBallotList() contains my votes.

                if ballot.vote is not None:
                    # If we had set a vote it was an own active vote
                    if vote is None:
                        logger.warning(
                            f"Found local vote but no vote in blind vote data. ballot={ballot}"
                        )
                    elif ballot.vote != vote:
                        logger.warning(
                            f"Found local vote but vote from blind vote does not match. ballot={ballot}, vote from blind vote={vote}"
                        )

                # Only include accepted/rejected votes
                if vote is not None:
                    ballots.append(Ballot(ballot.proposal, vote))
            else:
                # We got a vote but we don't have the ballot (which includes the proposal)
                # We add it to the missing list to handle it as exception later. We want all missing data so we
                # do not throw here.
                logger.warning(
                    f"Missing ballot for proposal with txId={tx_id}. Optional tx={self._dao_state_service.get_tx(tx_id)}"
                )
                missing_ballots.append(tx_id)

        if missing_ballots:
            raise VoteResultException.MissingBallotException(ballots, missing_ballots)

        # If we received a proposal after we had already voted we consider it as a proposal withhold attack and
        # treat the proposal as it was voted with a rejected vote.
        for tx_id, ballot in ballot_by_tx_id_map.items():
            if tx_id not in vote_by_tx_id_map:
                logger.warning(
                    f"Found proposal not in blind vote data - rejecting it. Proposal={ballot.proposal}",
                )
                ballots.append(Ballot(ballot.proposal, Vote(False)))

        # Let's keep the data more deterministic by sorting it by txId. Though we are not using the sorting.
        ballots.sort(key=lambda b: b.tx_id)
        return BallotList(ballots)

    def _get_stake_by_hash_of_blind_vote_list_map(
        self, decrypted_ballots_with_merits_set: set["DecryptedBallotsWithMerits"]
    ) -> dict[StorageByteArray, int]:
        stakes: dict[StorageByteArray, int] = {}
        for decrypted_ballots_with_merits in decrypted_ballots_with_merits_set:
            hash_bytes = StorageByteArray(
                decrypted_ballots_with_merits.hash_of_blind_vote_list
            )
            stakes.setdefault(hash_bytes, 0)
            # We must not use the merit(stake) as that is from the P2P network data and it is not guaranteed that we
            # have received it. We must rely only on blockchain data. The stake is from the vote reveal tx input.
            aggregated_stake = stakes[hash_bytes]
            stake = decrypted_ballots_with_merits.stake
            aggregated_stake += stake
            stakes[hash_bytes] = aggregated_stake

            logger.debug(
                f"blindVoteTxId={decrypted_ballots_with_merits.blind_vote_tx_id}, stake={stake}"
            )
        return stakes

    def _calculate_majority_blind_vote_list_hash(
        self, stakes: dict[StorageByteArray, int]
    ) -> bytes:
        stake_list = [
            HashWithStake(entry.bytes, stake) for entry, stake in stakes.items()
        ]
        return VoteResultConsensus.get_majority_hash(stake_list)

    # Deal with eventually consistency of P2P network
    def _find_blind_vote_list_matching_majority_hash(
        self, majority_vote_list_hash: bytes
    ) -> Optional[list["BlindVote"]]:
        # We reuse the method at voteReveal domain used when creating the hash
        blind_votes = BlindVoteConsensus.get_sorted_blind_vote_list_of_cycle(
            self._blind_vote_list_service
        )
        if self._is_list_matching_majority(majority_vote_list_hash, blind_votes, True):
            # Our local list is matching the majority hash
            return blind_votes
        else:
            logger.warning(
                "Our local list of blind vote payloads does not match the majorityVoteListHash. "
                "We try permuting our list to find a matching variant"
            )
            # Each voter has re-published his blind vote list when broadcasting the reveal tx so there should have a very
            # high chance that we have received all blind votes which have been used by the majority of the
            # voters (majority by stake).
            # It still could be that we have additional blind votes so our hash does not match. We can try to permute
            # our list with excluding items to see if we get a matching list. If not last resort is to request the
            # missing items from the network.
            permutated_list = self._find_permutated_list_matching_majority(
                majority_vote_list_hash
            )
            if permutated_list:
                return permutated_list
            else:
                logger.warning(
                    "We did not find a permutation of our blindVote list which matches the majority view. "
                    "We will request the blindVote data from the peers."
                )
                # This is async operation. We will restart the whole verification process once we received the data.
                self._missing_data_request_service.send_republish_request()
                return None

    def _find_permutated_list_matching_majority(
        self, majority_vote_list_hash: bytes
    ) -> Optional[list["BlindVote"]]:
        blind_vote_list = BlindVoteConsensus.get_sorted_blind_vote_list_of_cycle(
            self._blind_vote_list_service
        )
        ts = get_time_ms()

        def predicate(hash: bytes, variation: list["BlindVote"]):
            return self._is_list_matching_majority(hash, variation, False)

        result = PermutationUtil.find_matching_permutation(
            majority_vote_list_hash, blind_vote_list, predicate, 1000000
        )
        logger.info(
            f"findPermutatedListMatchingMajority for {len(blind_vote_list)} items took {get_time_ms() - ts} ms."
        )
        if not result:
            logger.info(
                "We did not find a variation of the blind vote list which matches the majority hash."
            )
            return None
        else:
            logger.info(
                f"We found a variation of the blind vote list which matches the majority hash. variation={result}"
            )
            return result

    def _is_list_matching_majority(
        self,
        majority_vote_list_hash: bytes,
        blind_vote_list: list["BlindVote"],
        do_log: bool,
    ) -> bool:
        hash_of_blind_vote_list = VoteRevealConsensus.get_hash_of_blind_vote_list(
            blind_vote_list
        )
        if do_log:
            logger.debug(
                f"majorityVoteListHash {bytes_as_hex_string(majority_vote_list_hash)}"
            )
            logger.debug(
                f"hashOfBlindVoteList {bytes_as_hex_string(hash_of_blind_vote_list)}"
            )
            logger.debug(
                f"List of blindVoteTxIds {', '.join(vote.tx_id for vote in blind_vote_list)}"
            )
        return majority_vote_list_hash == hash_of_blind_vote_list

    def _get_evaluated_proposals(
        self,
        decrypted_ballots_with_merits_set: set["DecryptedBallotsWithMerits"],
        chain_height: int,
    ) -> set["EvaluatedProposal"]:
        # We reorganize the data structure to have a map of proposals with a list of VoteWithStake objects
        vote_with_stake_by_proposal_map = (
            self._get_vote_with_stake_list_by_proposal_map(
                decrypted_ballots_with_merits_set
            )
        )

        evaluated_proposals = set["EvaluatedProposal"]()
        for proposal, vote_with_stake_list in vote_with_stake_by_proposal_map.items():
            required_quorum = self._dao_state_service.get_param_value_as_coin(
                proposal.get_quorum_param(), chain_height
            ).value
            required_vote_threshold = self._get_required_vote_threshold(
                chain_height, proposal
            )
            check_argument(
                required_vote_threshold >= 5000,
                "requiredVoteThreshold must be not be less than 50% otherwise we could have conflicting results.",
            )

            # move to consensus class
            proposal_vote_result = self._get_result_per_proposal(
                vote_with_stake_list, proposal
            )
            # Quorum is min. required BSQ stake to be considered valid
            reached_quorum = proposal_vote_result.quorum
            logger.debug(
                f"proposalTxId: {proposal.tx_id}, required requiredQuorum: {required_quorum}, requiredVoteThreshold: {required_vote_threshold / 100.0}"
            )
            if reached_quorum >= required_quorum:
                # We multiply by 10000 as we use a long for reachedThreshold and we want precision of 2 with
                # a % value. E.g. 50% is 5000.
                # Threshold is percentage of accepted to total stake
                reached_threshold = proposal_vote_result.threshold

                logger.debug(
                    f"reached threshold: {reached_threshold / 100.0} %, required threshold: {required_vote_threshold / 100.0} %"
                )
                # We need to exceed requiredVoteThreshold e.g. 50% is not enough but 50.01%.
                # Otherwise we could have 50% vs 50%
                if reached_threshold > required_vote_threshold:
                    evaluated_proposals.add(
                        EvaluatedProposal(True, proposal_vote_result)
                    )
                else:
                    evaluated_proposals.add(
                        EvaluatedProposal(False, proposal_vote_result)
                    )
                    logger.debug(
                        f"Proposal did not reach the requiredVoteThreshold. reachedThreshold={reached_threshold / 100.0} %, requiredVoteThreshold={required_vote_threshold / 100.0} %"
                    )
            else:
                evaluated_proposals.add(EvaluatedProposal(False, proposal_vote_result))
                logger.debug(
                    f"Proposal did not reach the requiredQuorum. reachedQuorum={reached_quorum}, requiredQuorum={required_quorum}"
                )

        evaluated_proposals_by_tx_id_map = {
            evaluated_proposal.proposal.tx_id: evaluated_proposal
            for evaluated_proposal in evaluated_proposals
        }

        # Proposals which did not get any vote need to be set as failed
        # JAVA TODO We should not use proposalListPresentation here.
        for (
            proposal
        ) in self._proposal_list_presentation.active_or_my_unconfirmed_proposals:
            if (
                self._period_service.is_tx_in_correct_cycle(
                    proposal.tx_id, chain_height
                )
                and proposal.tx_id not in evaluated_proposals_by_tx_id_map
            ):
                proposal_vote_result = ProposalVoteResult(
                    proposal, 0, 0, 0, 0, len(decrypted_ballots_with_merits_set)
                )
                evaluated_proposal = EvaluatedProposal(False, proposal_vote_result)
                evaluated_proposals.add(evaluated_proposal)
                logger.info(f"Proposal ignored by all voters: {evaluated_proposal}")

        # Check if our issuance sum is not exceeding the limit
        sum_issuance = sum(
            proposal.get_requested_bsq().value
            for proposal in (
                evaluated_proposal.proposal
                for evaluated_proposal in evaluated_proposals
                if evaluated_proposal.is_accepted
            )
            if isinstance(proposal, IssuanceProposal)
        )
        limit = self._dao_state_service.get_param_value_as_coin(
            Param.ISSUANCE_LIMIT, chain_height
        ).value
        if sum_issuance > limit:
            evaluated_proposals = {
                EvaluatedProposal(False, evaluated_proposal.proposal_vote_result)
                for evaluated_proposal in evaluated_proposals
                if evaluated_proposal.is_accepted
            }
            msg = (
                f"We have a total issuance amount of {sum_issuance / 100} BSQ but our limit for a cycle is {limit / 100} BSQ. "
                "We consider that cycle as invalid and have set all proposals as rejected."
            )
            logger.warning(msg)
            assert (
                self._dao_state_service.current_cycle is not None
            ), "daoStateService.getCurrentCycle() must not be null"

            self.vote_result_exceptions.append(
                VoteResultException(
                    self._dao_state_service.current_cycle,
                    VoteResultException.ConsensusException(msg),
                )
            )
            return evaluated_proposals

        return evaluated_proposals

    # We use long for calculation to avoid issues with rounding. So we multiply the % value as double (e.g. 0.5 = 50%)
    # by 100 to get the percentage value and again by 100 to get 2 decimal -> 5000 = 50.00%
    def _get_required_vote_threshold(
        self, chain_height: int, proposal: "Proposal"
    ) -> int:
        param_value_as_percent_double = (
            self._dao_state_service.get_param_value_as_percent_double(
                proposal.get_threshold_param(), chain_height
            )
        )
        return MathUtils.round_double_to_long(param_value_as_percent_double * 10000)

    def _get_vote_with_stake_list_by_proposal_map(
        self, decrypted_ballots_with_merits_set: set["DecryptedBallotsWithMerits"]
    ) -> dict["Proposal", list["VoteWithStake"]]:
        vote_with_stake_by_proposal_map: dict["Proposal", list["VoteWithStake"]] = {}
        for decrypted_ballots_with_merits in decrypted_ballots_with_merits_set:
            for ballot in decrypted_ballots_with_merits.ballot_list:
                proposal = ballot.proposal
                vote_with_stake_by_proposal_map.setdefault(proposal, [])
                vote_with_stake_list = vote_with_stake_by_proposal_map[proposal]
                sum_of_all_merits = MeritConsensus.get_merit_stake(
                    decrypted_ballots_with_merits.blind_vote_tx_id,
                    decrypted_ballots_with_merits.merit_list,
                    self._dao_state_service,
                )
                vote_with_stake = VoteWithStake(
                    ballot.vote, decrypted_ballots_with_merits.stake, sum_of_all_merits
                )
                vote_with_stake_list.append(vote_with_stake)
                logger.debug(
                    f"Add entry to vote_with_stake_list_by_proposal_map: proposalTxId={proposal.tx_id}, voteWithStake={vote_with_stake}"
                )
        return vote_with_stake_by_proposal_map

    def _get_result_per_proposal(
        self, vote_with_stake_list: list["VoteWithStake"], proposal: "Proposal"
    ) -> "ProposalVoteResult":
        num_accepted_votes = 0
        num_rejected_votes = 0
        num_ignored_votes = 0
        stake_of_accepted_votes = 0
        stake_of_rejected_votes = 0

        for vote_with_stake in vote_with_stake_list:
            sum_of_all_merits = vote_with_stake.sum_of_all_merits
            stake = vote_with_stake.stake
            combined_stake = stake + sum_of_all_merits
            logger.debug(
                f"proposalTxId={proposal.tx_id}, stake={stake}, sumOfAllMerits={sum_of_all_merits}, combinedStake={combined_stake}"
            )
            vote = vote_with_stake.vote
            if vote is not None:
                if vote.accepted:
                    stake_of_accepted_votes += combined_stake
                    num_accepted_votes += 1
                else:
                    stake_of_rejected_votes += combined_stake
                    num_rejected_votes += 1
            else:
                num_ignored_votes += 1
                logger.debug("Voter ignored proposal")

        return ProposalVoteResult(
            proposal,
            stake_of_accepted_votes,
            stake_of_rejected_votes,
            num_accepted_votes,
            num_rejected_votes,
            num_ignored_votes,
        )

    def _apply_accepted_proposals(
        self, accepted_evaluated_proposals: set["EvaluatedProposal"], chain_height: int
    ):
        self._apply_issuance(accepted_evaluated_proposals, chain_height)
        self._apply_param_change(accepted_evaluated_proposals, chain_height)
        self._apply_bonded_role(accepted_evaluated_proposals)
        self._apply_confiscate_bond(accepted_evaluated_proposals)
        self._apply_remove_asset(accepted_evaluated_proposals)

    def _apply_issuance(
        self, accepted_evaluated_proposals: set["EvaluatedProposal"], chain_height: int
    ):
        for evaluated_proposal in accepted_evaluated_proposals:
            if isinstance(evaluated_proposal.proposal, IssuanceProposal):
                issuance_proposal = evaluated_proposal.proposal
                self._issuance_service.issue_bsq(issuance_proposal, chain_height)

    def _apply_param_change(
        self, accepted_evaluated_proposals: set["EvaluatedProposal"], chain_height: int
    ):
        evaluated_proposals_by_param: dict[str, list["EvaluatedProposal"]] = {}
        for evaluated_proposal in accepted_evaluated_proposals:
            if isinstance(evaluated_proposal.proposal, ChangeParamProposal):
                change_param_proposal = evaluated_proposal.proposal
                param_change = self._get_param_change(
                    change_param_proposal, chain_height
                )
                if param_change:
                    param_name = param_change.param_name
                    evaluated_proposals_by_param.setdefault(param_name, [])
                    evaluated_proposals_by_param[param_name].append(evaluated_proposal)

        for param_name, proposals in evaluated_proposals_by_param.items():
            if len(proposals) == 1:
                self._apply_accepted_change_param_proposal(
                    proposals[0].proposal, chain_height
                )
            elif len(proposals) > 1:
                logger.warning(
                    "There have been multiple winning param change proposals with the same item. "
                    "This is a sign of a social consensus failure. "
                    "We treat all requests as failed in such a case."
                )

    def _apply_accepted_change_param_proposal(
        self, change_param_proposal: "ChangeParamProposal", chain_height: int
    ):
        msg = (
            "\n################################################################################\n"
            f"We changed a parameter. ProposalTxId={change_param_proposal.tx_id}\n"
            f"Param: {change_param_proposal.param.name} new value: {change_param_proposal.param_value}\n"
            "################################################################################\n"
        )
        logger.info(msg)

        self._dao_state_service.set_new_param(
            chain_height, change_param_proposal.param, change_param_proposal.param_value
        )

    def _get_param_change(
        self, change_param_proposal: "ChangeParamProposal", chain_height: int
    ) -> Optional[ParamChange]:
        height_of_new_cycle = self._dao_state_service.get_start_height_of_next_cycle(
            chain_height
        )
        if height_of_new_cycle is not None:
            return ParamChange(
                change_param_proposal.param.name,
                change_param_proposal.param_value,
                height_of_new_cycle,
            )
        return None

    def _apply_bonded_role(
        self, accepted_evaluated_proposals: set["EvaluatedProposal"]
    ):
        for evaluated_proposal in accepted_evaluated_proposals:
            if isinstance(evaluated_proposal.proposal, RoleProposal):
                role_proposal = evaluated_proposal.proposal
                role = role_proposal.role
                msg = (
                    "\n################################################################################\n"
                    f"We added a bonded role. ProposalTxId={role_proposal.tx_id}\n"
                    f"Role: {role.display_string}\n"
                    "################################################################################\n"
                )
                logger.info(msg)

    def _apply_confiscate_bond(
        self, accepted_evaluated_proposals: set["EvaluatedProposal"]
    ):
        for evaluated_proposal in accepted_evaluated_proposals:
            if isinstance(evaluated_proposal.proposal, ConfiscateBondProposal):
                confiscate_bond_proposal = evaluated_proposal.proposal
                self._dao_state_service.confiscate_bond(
                    confiscate_bond_proposal.lockup_tx_id
                )

                msg = (
                    "\n################################################################################\n"
                    f"We confiscated a bond. ProposalTxId={confiscate_bond_proposal.tx_id}\n"
                    f"LockupTxId: {confiscate_bond_proposal.lockup_tx_id}\n"
                    "################################################################################\n"
                )
                logger.info(msg)

    def _apply_remove_asset(
        self, accepted_evaluated_proposals: set["EvaluatedProposal"]
    ):
        for evaluated_proposal in accepted_evaluated_proposals:
            if isinstance(evaluated_proposal.proposal, RemoveAssetProposal):
                remove_asset_proposal = evaluated_proposal.proposal
                ticker_symbol = remove_asset_proposal.ticker_symbol
                msg = (
                    "\n################################################################################\n"
                    f"We removed an asset. ProposalTxId={remove_asset_proposal.tx_id}\n"
                    f"Asset: {ticker_symbol}\n"
                    "################################################################################\n"
                )
                logger.info(msg)

    def _get_accepted_evaluated_proposals(
        self, evaluated_proposals: set["EvaluatedProposal"]
    ) -> set["EvaluatedProposal"]:
        return {proposal for proposal in evaluated_proposals if proposal.is_accepted}

    def _is_in_vote_result_phase(self, chain_height: int) -> bool:
        return (
            self._period_service.get_first_block_of_phase(
                chain_height, DaoPhase.Phase.RESULT
            )
            == chain_height
        )


@dataclass(frozen=True)
class HashWithStake:
    hash: bytes
    stake: int

    def __str__(self):
        return (
            f"HashWithStake{{\n"
            f"     hash={bytes_as_hex_string(self.hash)},\n"
            f"     stake={self.stake}\n"
            f"}}"
        )


@dataclass(frozen=True)
class VoteWithStake:
    vote: Optional[Vote]
    stake: int
    sum_of_all_merits: int

    def __str__(self):
        return (
            f"VoteWithStake{{\n"
            f"     vote={self.vote},\n"
            f"     stake={self.stake},\n"
            f"     sumOfAllMerits={self.sum_of_all_merits}\n"
            f"}}"
        )
