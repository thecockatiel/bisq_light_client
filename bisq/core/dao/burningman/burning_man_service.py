from collections.abc import Callable, Collection
from typing import TYPE_CHECKING

from bisq.core.dao.burningman.model.burn_output_model import BurnOutputModel
from bisq.core.dao.burningman.model.compensation_model import CompensationModel
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate
from bisq.core.dao.governance.proofofburn.proof_of_burn_consensus import (
    ProofOfBurnConsensus,
)
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray


if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.dao.state.model.governance.issuance import Issuance
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService
    from bisq.core.dao.cycles_in_dao_state_service import CyclesInDaoStateService
    from bisq.core.dao.state.dao_state_service import DaoStateService


class BurningManService:
    """
    Methods are used by the DelayedPayoutTxReceiverService, which is used in the trade protocol for creating and
    verifying the delayed payout transaction. As verification is done by trade peer it requires data to be deterministic.
    Parameters listed here must not be changed as they could break verification of the peers
    delayed payout transaction in case not both traders are using the same version.
    """

    # Parameters
    # Cannot be changed after release as it would break trade protocol verification of DPT receivers.

    # Prefix for generic names for the genesis outputs. Appended with output index.
    # Used as pre-image for burning.
    GENESIS_OUTPUT_PREFIX = "Bisq co-founder "

    # Factor for weighting the genesis output amounts.
    GENESIS_OUTPUT_AMOUNT_FACTOR = 0.1

    # The number of cycles we go back for the decay function used for compensation request amounts.
    NUM_CYCLES_COMP_REQUEST_DECAY = 24

    # The number of cycles we go back for the decay function used for burned amounts.
    NUM_CYCLES_BURN_AMOUNT_DECAY = 12

    # Factor for boosting the issuance share (issuance is compensation requests + genesis output).
    # This will be used for increasing the allowed burn amount. The factor gives more flexibility
    # and compensates for those who do not burn. The burn share is capped by that factor as well.
    # E.g. a contributor with 1% issuance share will be able to receive max 10% of the BTC fees or DPT output
    # even if they had burned more and had a higher burn share than 10%.
    ISSUANCE_BOOST_FACTOR = 10

    # The max amount the burn share can reach. This value is derived from the min. security deposit in a trade and
    # ensures that an attack where a BM would take all sell offers cannot be economically profitable as they would
    # lose their deposit and cannot gain more than 11% of the DPT payout. As the total amount in a trade is 2 times
    # that deposit plus the trade amount the limiting factor here is 11% (0.15 / 1.3).
    MAX_BURN_SHARE = 0.11

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        cycles_in_dao_state_service: "CyclesInDaoStateService",
        proposal_service: "ProposalService",
    ) -> None:
        self._dao_state_service = dao_state_service
        self._cycles_in_dao_state_service = cycles_in_dao_state_service
        self._proposal_service = proposal_service

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Package scope API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_burning_man_candidates_by_name(
        self, chain_height: int, limit_capping_rounds: bool = False
    ):
        burning_man_candidates_by_name: dict[str, "BurningManCandidate"] = {}
        proof_of_burn_op_return_tx_output_by_hash = (
            self.get_proof_of_burn_op_return_tx_output_by_hash(chain_height)
        )

        def process_contributors(
            issuance: "Issuance", compensation_proposal: "CompensationProposal"
        ):
            name = compensation_proposal.name
            candidate = burning_man_candidates_by_name.setdefault(
                name, BurningManCandidate()
            )

            # Issuance
            custom_address = compensation_proposal.get_burning_man_receiver_address()
            is_custom_address = custom_address is not None
            if is_custom_address:
                receiver_address = custom_address
            else:
                # We take change address from compensation request
                receiver_address = self._get_address_from_compensation_request(
                    self._dao_state_service.get_tx(compensation_proposal.tx_id)
                )

            if receiver_address:
                issuance_height = issuance.chain_height
                issuance_amount = self._get_issuance_amount_for_compensation_request(
                    issuance
                )
                cycle_index = (
                    self._cycles_in_dao_state_service.get_cycle_index_at_chain_height(
                        issuance_height
                    )
                )
                if self._is_valid_compensation_request(
                    name, cycle_index, issuance_amount
                ):
                    decayed_issuance_amount = self._get_decayed_compensation_amount(
                        issuance_amount, issuance_height, chain_height
                    )
                    issuance_date = self._dao_state_service.get_block_time(
                        issuance_height
                    )
                    candidate.add_compensation_model(
                        CompensationModel.from_compensation_request(
                            receiver_address,
                            is_custom_address,
                            issuance_amount,
                            decayed_issuance_amount,
                            issuance_height,
                            issuance.tx_id,
                            issuance_date,
                            cycle_index,
                        )
                    )
            self._add_burn_output_model(
                chain_height, proof_of_burn_op_return_tx_output_by_hash, name, candidate
            )

        # Add contributors who made a compensation request
        self._for_each_compensation_issuance(chain_height, process_contributors)

        # Add output receivers of genesis transaction
        genesis_tx = self._dao_state_service.get_genesis_tx()
        if genesis_tx:
            for tx_output in genesis_tx.tx_outputs:
                name = f"{BurningManService.GENESIS_OUTPUT_PREFIX}{tx_output.index}"
                if name not in burning_man_candidates_by_name:
                    burning_man_candidates_by_name[name] = BurningManCandidate()
                candidate = burning_man_candidates_by_name[name]

                # Issuance
                issuance_height = tx_output.block_height
                issuance_amount = tx_output.value
                decayed_amount = self._get_decayed_genesis_output_amount(
                    issuance_amount
                )
                issuance_date = self._dao_state_service.get_block_time(issuance_height)
                candidate.add_compensation_model(
                    CompensationModel.from_genesis_output(
                        tx_output.address,
                        issuance_amount,
                        decayed_amount,
                        issuance_height,
                        tx_output.tx_id,
                        tx_output.index,
                        issuance_date,
                    )
                )
                self._add_burn_output_model(
                    chain_height,
                    proof_of_burn_op_return_tx_output_by_hash,
                    name,
                    candidate,
                )

        burning_man_candidates = burning_man_candidates_by_name.values()
        total_decayed_compensation_amounts = sum(
            candidate.accumulated_decayed_compensation_amount
            for candidate in burning_man_candidates
        )
        total_decayed_burn_amounts = sum(
            candidate.accumulated_decayed_burn_amount
            for candidate in burning_man_candidates
        )
        for candidate in burning_man_candidates:
            candidate.calculate_shares(
                total_decayed_compensation_amounts, total_decayed_burn_amounts
            )

        num_rounds_with_caps_applied = self._impose_caps(
            burning_man_candidates, limit_capping_rounds
        )

        sum_all_capped_burn_amount_shares = sum(
            candidate.get_max_boosted_compensation_share()
            for candidate in burning_man_candidates
            if candidate.round_capped is not None
        )
        sum_all_non_capped_burn_amount_shares = sum(
            candidate.burn_amount_share
            for candidate in burning_man_candidates
            if candidate.round_capped is None
        )
        for candidate in burning_man_candidates:
            candidate.calculate_capped_and_adjusted_shares(
                sum_all_capped_burn_amount_shares,
                sum_all_non_capped_burn_amount_shares,
                num_rounds_with_caps_applied,
            )

        return burning_man_candidates_by_name

    def get_legacy_burning_man_address(self, chain_height: int) -> str:
        return self._dao_state_service.get_param_value(
            Param.RECIPIENT_BTC_ADDRESS, chain_height
        )

    def get_active_burning_man_candidates(
        self, chain_height: int, limit_capping_rounds: bool = False
    ):
        return [
            candidate
            for candidate in self.get_burning_man_candidates_by_name(
                chain_height, limit_capping_rounds
            ).values()
            if candidate.capped_burn_amount_share > 0
            and candidate.is_receiver_address_valid()
        ]

    def get_proof_of_burn_op_return_tx_output_by_hash(self, chain_height: int):
        result: dict["StorageByteArray", set["TxOutput"]] = {}
        for (
            tx_output
        ) in self._dao_state_service.get_proof_of_burn_op_return_tx_outputs():
            if tx_output.block_height <= chain_height:
                key = StorageByteArray(
                    ProofOfBurnConsensus.get_hash_from_op_return_data(
                        tx_output.op_return_data
                    )
                )
                if key not in result:
                    result[key] = set()
                result[key].add(tx_output)
        return result

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _for_each_compensation_issuance(
        self,
        chain_height: int,
        action: Callable[["Issuance", "CompensationProposal"], None],
    ) -> None:
        for proposal_payload in self._proposal_service.proposal_payloads:
            proposal = proposal_payload.proposal
            if isinstance(proposal, CompensationProposal):
                issuance = self._dao_state_service.get_issuance(proposal.tx_id)
                if issuance and issuance.chain_height <= chain_height:
                    action(issuance, proposal)

    def _get_address_from_compensation_request(self, tx: "Tx") -> str:
        tx_outputs = tx.tx_outputs
        # The compensation request tx has usually 4 outputs. If there is no BTC change its 3 outputs.
        # BTC change output is at index 2 if present otherwise
        # we use the BSQ address of the compensation candidate output at index 1.
        # See https://docs.bisq.network/dao-technical-overview.html#compensation-request-txreimbursement-request-tx
        if len(tx_outputs) == 4:
            return tx_outputs[2].address
        else:
            return tx_outputs[1].address

    def _get_issuance_amount_for_compensation_request(
        self, issuance: "Issuance"
    ) -> int:
        # There was a reimbursement for a conference sponsorship with 44776 BSQ. We remove that as well.
        # See https://github.com/bisq-network/compensation/issues/498
        if (
            issuance.tx_id
            == "01455fc4c88fca0665a5f56a90ff03fb9e3e88c3430ffc5217246e32d180aa64"
        ):
            return 119400  # That was the compensation part
        else:
            return issuance.amount

    def _is_valid_compensation_request(
        self, name: str, cycle_index: int, issuance_amount: int
    ) -> bool:
        # Up to cycle 15 the RefundAgent made reimbursement requests as compensation requests. We filter out those entries.
        # As it is mixed with RefundAgents real compensation requests we take out all above 3500 BSQ.
        is_reimbursement_of_refund_agent = (
            name == "RefundAgent" and cycle_index <= 15 and issuance_amount > 350000
        )
        return not is_reimbursement_of_refund_agent

    def _get_decayed_compensation_amount(
        self, amount: int, issuance_height: int, chain_height: int
    ) -> int:
        chain_height_of_past_cycle = (
            self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
                chain_height, BurningManService.NUM_CYCLES_COMP_REQUEST_DECAY
            )
        )
        return BurningManService._get_decayed_amount(
            amount, issuance_height, chain_height, chain_height_of_past_cycle
        )

    # Linear decay between currentBlockHeight (100% of amount) and issuanceHeight
    # chainHeightOfPastCycle is currentBlockHeight - numCycles*cycleDuration. It changes with each block and
    # distance to currentBlockHeight is the same if cycle durations have not changed (possible via DAo voting but never done).
    @staticmethod
    def _get_decayed_amount(
        amount: int,
        issuance_height: int,
        current_block_height: int,
        chain_height_of_past_cycle: int,
    ) -> int:

        if issuance_height > current_block_height:
            raise IllegalArgumentException(
                f"issuance_height must not be larger than current_block_height. issuance_height={issuance_height}; current_block_height={current_block_height}"
            )
        if current_block_height < 0:
            raise IllegalArgumentException(
                f"current_block_height must not be negative. current_block_height={current_block_height}"
            )
        if amount < 0:
            raise IllegalArgumentException(
                f"amount must not be negative. amount={amount}"
            )
        if issuance_height < 0:
            raise IllegalArgumentException(
                f"issuance_height must not be negative. issuance_height={issuance_height}"
            )

        if current_block_height <= chain_height_of_past_cycle:
            return amount

        factor = max(
            0,
            (issuance_height - chain_height_of_past_cycle)
            / (current_block_height - chain_height_of_past_cycle),
        )
        weighted = round(amount * factor)
        return max(0, weighted)

    def _add_burn_output_model(
        self,
        chain_height: int,
        proof_of_burn_op_return_tx_output_by_hash: dict[
            "StorageByteArray", set["TxOutput"]
        ],
        name: str,
        candidate: "BurningManCandidate",
    ) -> None:
        for burn_output in self._get_proof_of_burn_op_return_tx_output_set_for_name(
            proof_of_burn_op_return_tx_output_by_hash, name
        ):
            burn_output_height = burn_output.block_height
            optional_tx = self._dao_state_service.get_tx(burn_output.tx_id)
            if optional_tx:
                burn_output_amount = optional_tx.burnt_bsq
            else:
                burn_output_amount = 0

            decayed_burn_output_amount = self._get_decayed_burned_amount(
                burn_output_amount, burn_output_height, chain_height
            )
            if optional_tx:
                date = optional_tx.time
            else:
                date = 0
            cycle_index = (
                self._cycles_in_dao_state_service.get_cycle_index_at_chain_height(
                    burn_output_height
                )
            )
            candidate.add_burn_output_model(
                BurnOutputModel(
                    burn_output_amount,
                    decayed_burn_output_amount,
                    burn_output_height,
                    burn_output.tx_id,
                    date,
                    cycle_index,
                )
            )

    @staticmethod
    def _get_proof_of_burn_op_return_tx_output_set_for_name(
        proof_of_burn_op_return_tx_output_by_hash: dict[
            "StorageByteArray", set["TxOutput"]
        ],
        name: str,
    ) -> set["TxOutput"]:
        pre_image = name.encode("utf-8")
        hash_ = ProofOfBurnConsensus.get_hash(pre_image)
        key = StorageByteArray(hash_)
        return proof_of_burn_op_return_tx_output_by_hash.get(key, set())

    def _get_decayed_burned_amount(
        self, amount: int, issuance_height: int, chain_height: int
    ) -> int:
        chain_height_of_past_cycle = (
            self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
                chain_height, BurningManService.NUM_CYCLES_BURN_AMOUNT_DECAY
            )
        )
        return self._get_decayed_amount(
            amount, issuance_height, chain_height, chain_height_of_past_cycle
        )

    def _get_decayed_genesis_output_amount(self, amount: int) -> int:
        return round(amount * BurningManService.GENESIS_OUTPUT_AMOUNT_FACTOR)

    @staticmethod
    def _impose_caps(
        burning_man_candidates: Collection["BurningManCandidate"],
        limit_capping_rounds: bool,
    ) -> int:
        candidates_in_descending_burn_cap_ratio = sorted(
            burning_man_candidates, key=lambda c: c.get_burn_cap_ratio(), reverse=True
        )
        threshold_burn_cap_ratio = 1.0
        remaining_burn_share = 1.0
        remaining_cap_share = 1.0
        capping_round = 0

        for candidate in candidates_in_descending_burn_cap_ratio:
            inv_scale_factor = remaining_burn_share / remaining_cap_share
            burn_cap_ratio = candidate.get_burn_cap_ratio()

            if (
                remaining_cap_share <= 0.0
                or burn_cap_ratio <= 0.0
                or burn_cap_ratio < inv_scale_factor
                or (limit_capping_rounds and burn_cap_ratio < 1.0)
            ):
                capping_round += 1
                break

            if burn_cap_ratio < threshold_burn_cap_ratio:
                threshold_burn_cap_ratio = inv_scale_factor
                capping_round += 1

            candidate.impose_cap(
                capping_round, candidate.burn_amount_share / threshold_burn_cap_ratio
            )
            remaining_burn_share -= candidate.burn_amount_share
            remaining_cap_share -= candidate.get_max_boosted_compensation_share()

        return capping_round
