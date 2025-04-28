from collections.abc import Collection
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.common.config.config import Config
from bisq.core.dao.burningman.burning_man_presentation_service import (
    BurningManPresentationService,
)
from bisq.core.dao.burningman.model.reimbursement_model import ReimbursementModel
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from utils.python_helpers import classproperty

if TYPE_CHECKING:
    from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.dao.state.model.governance.cycle import Cycle
    from bisq.core.dao.state.model.governance.issuance import Issuance
    from bisq.core.dao.cycles_in_dao_state_service import CyclesInDaoStateService
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService
    from bisq.core.dao.state.dao_state_service import DaoStateService
 


class BurnTargetService:
    """
    Burn target related API. Not touching trade protocol aspects and parameters can be changed here without risking to
    break trade protocol validations.
    """

    # Number of cycles for accumulating reimbursement amounts. Used for the burn target.
    NUM_CYCLES_BURN_TARGET = 12
    NUM_CYCLES_AVERAGE_DISTRIBUTION = 3

    @classproperty
    def ACTIVATION_BLOCK(cls):
        # Estimated block at activation date
        return 111 if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest() else 769845

    # Default value for the estimated BTC trade fees per month as BSQ sat value (100 sat = 1 BSQ).
    # Default is roughly average of last 12 months at Nov 2022.
    # Can be changed with DAO parameter voting.
    DEFAULT_ESTIMATED_BTC_TRADE_FEE_REVENUE_PER_CYCLE = 620000000

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        cycles_in_dao_state_service: "CyclesInDaoStateService",
        proposal_service: "ProposalService",
    ):
        self.logger = get_ctx_logger(__name__)
        self._dao_state_service = dao_state_service
        self._cycles_in_dao_state_service = cycles_in_dao_state_service
        self._proposal_service = proposal_service

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_reimbursements(self, chain_height: int) -> set["ReimbursementModel"]:
        reimbursements = set["ReimbursementModel"]()
        issuances = self._dao_state_service.get_issuance_set_for_type(
            IssuanceType.REIMBURSEMENT
        )
        for issuance in filter(lambda i: i.chain_height <= chain_height, issuances):
            for (
                reimbursement_proposal
            ) in self._get_reimbursement_proposals_for_issuance(issuance):
                issuance_height = issuance.chain_height
                issuance_amount = issuance.amount
                issuance_date = self._dao_state_service.get_block_time(issuance_height)
                cycle_index = (
                    self._cycles_in_dao_state_service.get_cycle_index_at_chain_height(
                        issuance_height
                    )
                )
                reimbursements.add(
                    ReimbursementModel(
                        issuance_amount,
                        issuance_height,
                        issuance_date,
                        cycle_index,
                        reimbursement_proposal.tx_id,
                    )
                )
        return reimbursements

    def get_burn_target(
        self, chain_height: int, burning_man_candidates: Collection["BurningManCandidate"]
    ) -> int:
        # Reimbursements are taken into account at result vote block
        chain_height_of_past_cycle = (
            self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
                chain_height, BurnTargetService.NUM_CYCLES_BURN_TARGET
            )
        )
        accumulated_reimbursements = self._get_adjusted_accumulated_reimbursements(
            chain_height, chain_height_of_past_cycle
        )

        # Param changes are taken into account at first block at next cycle after voting
        height_of_first_block_of_past_cycle = (
            self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
                chain_height, BurnTargetService.NUM_CYCLES_BURN_TARGET - 1
            )
        )
        accumulated_estimated_btc_trade_fees = (
            self._get_accumulated_estimated_btc_trade_fees(
                chain_height, height_of_first_block_of_past_cycle
            )
        )

        # Legacy BurningMan
        proof_of_burn_txs = self._get_proof_of_burn_txs(
            chain_height, chain_height_of_past_cycle
        )
        burned_amount_from_legacy_burningman_dpt = (
            self._get_burned_amount_from_legacy_burningman_dpt(
                proof_of_burn_txs, chain_height, chain_height_of_past_cycle
            )
        )
        burned_amount_from_legacy_burningmans_btc_fees = (
            self._get_burned_amount_from_legacy_burningmans_btc_fees(
                proof_of_burn_txs, chain_height, chain_height_of_past_cycle
            )
        )

        # Distributed BurningMen
        burned_amount_from_burning_men = self._get_burned_amount_from_burning_men(
            burning_man_candidates, chain_height, chain_height_of_past_cycle
        )

        burn_target = (
            accumulated_reimbursements
            + accumulated_estimated_btc_trade_fees
            - burned_amount_from_legacy_burningman_dpt
            - burned_amount_from_legacy_burningmans_btc_fees
            - burned_amount_from_burning_men
        )

        self.logger.info(
            f"accumulated_reimbursements: {accumulated_reimbursements}\n"
            f"+ accumulated_estimated_btc_trade_fees: {accumulated_estimated_btc_trade_fees}\n"
            f"- burned_amount_from_legacy_burningman_dpt: {burned_amount_from_legacy_burningman_dpt}\n"
            f"- burned_amount_from_legacy_burningmans_btc_fees: {burned_amount_from_legacy_burningmans_btc_fees}\n"
            f"- burned_amount_from_burning_men: {burned_amount_from_burning_men}\n"
            f"= burn_target: {burn_target}\n",
        )
        return burn_target

    def get_average_distribution_per_cycle(self, chain_height: int) -> int:
        # Reimbursements are taken into account at result vote block
        chain_height_of_past_cycle = (
            self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
                chain_height, BurnTargetService.NUM_CYCLES_AVERAGE_DISTRIBUTION
            )
        )
        reimbursements = self._get_adjusted_accumulated_reimbursements(
            chain_height, chain_height_of_past_cycle
        )

        # Param changes are taken into account at first block at next cycle after voting
        first_block_of_past_cycle = (
            self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
                chain_height, BurnTargetService.NUM_CYCLES_AVERAGE_DISTRIBUTION - 1
            )
        )
        btc_trade_fees = self._get_accumulated_estimated_btc_trade_fees(
            chain_height, first_block_of_past_cycle
        )

        return round(
            (reimbursements + btc_trade_fees)
            / BurnTargetService.NUM_CYCLES_AVERAGE_DISTRIBUTION
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_reimbursement_proposals_for_issuance(self, issuance: "Issuance"):
        return (
            pp.proposal
            for pp in self._proposal_service.proposal_payloads
            if issuance.tx_id == pp.proposal.tx_id
            and isinstance(pp.proposal, ReimbursementModel)
        )

    def _get_adjusted_accumulated_reimbursements(
        self, chain_height: int, from_block: int
    ) -> int:
        reimbursements = self.get_reimbursements(chain_height)
        total_adjusted_amount = 0

        for reimbursement in reimbursements:
            if from_block < reimbursement.height <= chain_height:
                amount = reimbursement.amount
                if reimbursement.height > BurnTargetService.ACTIVATION_BLOCK:
                    # As we do not pay out the losing party's security deposit we adjust this here.
                    # We use 15% as the min. security deposit as we do not have the detail data.
                    # A trade with 1 BTC has 1.3 BTC in the DPT which goes to BM. The reimbursement is
                    # only BSQ equivalent to 1.15 BTC. So we map back  the 1.15 BTC to 1.3 BTC to account for
                    # that what the BM received.
                    # There are multiple unknowns included:
                    # - Real security deposit can be higher
                    # - Refund agent can make a custom payout, paying out more or less than expected
                    # - BSQ/BTC volatility
                    # - Delay between DPT and reimbursement
                    adjusted_amount = round(amount * 1.3 / 1.15)
                    total_adjusted_amount += adjusted_amount
                else:
                    # For old reimbursements we do not apply the adjustment as we had a different policy for
                    # reimbursing out 100% of the DPT.
                    total_adjusted_amount += amount

        return total_adjusted_amount

    # The BTC fees are set by parameter and becomes active at first block of the next cycle after voting.
    def _get_accumulated_estimated_btc_trade_fees(
        self, chain_height: int, from_block: int
    ) -> int:
        cycles = self._dao_state_service.cycles
        return sum(
            self._get_btc_trade_fee_from_param(cycle)
            for cycle in cycles
            # TODO: java has this <=, but since rest of the file was already <, we also made it <
            # this needs to be checked later when https://github.com/bisq-network/bisq/issues/7400
            # is resolved
            if from_block < cycle.height_of_first_block <= chain_height
        )

    def _get_btc_trade_fee_from_param(self, cycle: "Cycle") -> int:
        value = self._dao_state_service.get_param_value_as_block(
            Param.LOCK_TIME_TRADE_PAYOUT, cycle.height_of_first_block
        )
        # Ignore default value (4320)
        return (
            value
            if value != 4320
            else BurnTargetService.DEFAULT_ESTIMATED_BTC_TRADE_FEE_REVENUE_PER_CYCLE
        )

    def _get_proof_of_burn_txs(self, chain_height: int, from_block: int):
        return {
            tx
            for tx in self._dao_state_service.get_proof_of_burn_txs()
            if from_block < tx.block_height <= chain_height
        }

    def _get_burned_amount_from_legacy_burningman_dpt(
        self, proof_of_burn_txs: set["Tx"], chain_height: int, from_block: int
    ) -> int:
        # Legacy burningman use those opReturn data to mark their burn transactions from delayed payout transaction cases.
        # opReturn data from delayed payout txs when BM traded with the refund agent: 1701e47e5d8030f444c182b5e243871ebbaeadb5e82f
        # opReturn data from delayed payout txs when BM traded with traders who got reimbursed by the DAO: 1701293c488822f98e70e047012f46f5f1647f37deb7
        return sum(
            tx.burnt_bsq
            for tx in proof_of_burn_txs
            if from_block < tx.block_height <= chain_height
            and tx.last_tx_output.op_return_data.hex()
            in BurningManPresentationService.OP_RETURN_DATA_LEGACY_BM_DPT
        )

    def _get_burned_amount_from_legacy_burningmans_btc_fees(
        self, proof_of_burn_txs: set["Tx"], chain_height: int, from_block: int
    ) -> int:
        # Legacy burningman use the below opReturn data to mark their burn transactions from Btc trade fees.

        return sum(
            tx.burnt_bsq
            for tx in proof_of_burn_txs
            if from_block < tx.block_height <= chain_height
            and tx.last_tx_output.op_return_data.hex()
            in BurningManPresentationService.OP_RETURN_DATA_LEGACY_BM_FEES
        )

    def _get_burned_amount_from_burning_men(
        self,
        burning_man_candidates: Collection["BurningManCandidate"],
        chain_height: int,
        from_block: int,
    ) -> int:
        return sum(
            burn_output_model.amount
            for burning_man_candidate in burning_man_candidates
            for burn_output_model in burning_man_candidate.burn_output_models
            if from_block < burn_output_model.height <= chain_height
        )

    def get_accumulated_decayed_burned_amount(
        self, burning_man_candidates: Collection["BurningManCandidate"], chain_height: int
    ) -> int:
        from_block = self._cycles_in_dao_state_service.get_chain_height_of_past_cycle(
            chain_height, BurnTargetService.NUM_CYCLES_BURN_TARGET
        )
        return self._get_accumulated_decayed_burned_amount(
            burning_man_candidates, chain_height, from_block
        )

    def _get_accumulated_decayed_burned_amount(
        self,
        burning_man_candidates: Collection["BurningManCandidate"],
        chain_height: int,
        from_block: int,
    ) -> int:
        return sum(
            sum(
                burn_output_model.decayed_amount
                for burn_output_model in burning_man_candidate.burn_output_models
                if from_block < burn_output_model.height <= chain_height
            )
            for burning_man_candidate in burning_man_candidates
        )
