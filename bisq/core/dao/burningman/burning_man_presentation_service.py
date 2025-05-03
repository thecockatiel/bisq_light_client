from datetime import datetime
from typing import TYPE_CHECKING, Optional
from bisq.common.config.config import Config
from bisq.core.dao.burningman.model.burn_output_model import BurnOutputModel
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from utils.python_helpers import classproperty
from bisq.core.dao.burningman.burning_man_service import BurningManService
from bisq.core.dao.burningman.model.legacy_burning_man import LegacyBurningMan

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.governance.proposal.my_proposal_list_service import (
        MyProposalListService,
    )
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.cycles_in_dao_state_service import CyclesInDaoStateService
    from bisq.core.dao.burningman.model.reimbursement_model import ReimbursementModel
    from bisq.core.dao.burningman.burn_target_service import BurnTargetService
    from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.state.dao_state_service import DaoStateService


class BurningManPresentationService(DaoStateListener):
    """Provides APIs for burningman data representation in the UI."""

    # Burn target gets increased by that amount to give more flexibility.
    # Burn target is calculated from reimbursements + estimated BTC fees - burned amounts.
    BURN_TARGET_BOOST_AMOUNT = 10000000
    LEGACY_BURNING_MAN_DPT_NAME = "Legacy Burningman (DPT)"
    LEGACY_BURNING_MAN_BTC_FEES_NAME = "Legacy Burningman (BTC fees)"
    LEGACY_BURNING_MAN_BTC_FEES_ADDRESS = "38bZBj5peYS3Husdz7AH3gEUiUbYRD951t"

    @classproperty
    def OP_RETURN_DATA_LEGACY_BM_DPT(cls):
        # Those are the opReturn data used by legacy BM for burning BTC received from DPT.
        # For regtest testing burn bsq and use the pre-image `dpt` which has the hash 14af04ea7e34bd7378b034ddf90da53b7c27a277.
        # The opReturn data gets additionally prefixed with 1701
        return (
            {"170114af04ea7e34bd7378b034ddf90da53b7c27a277"}
            if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest()
            else {
                "1701e47e5d8030f444c182b5e243871ebbaeadb5e82f",
                "1701293c488822f98e70e047012f46f5f1647f37deb7",
            }
        )

    @classproperty
    def OP_RETURN_DATA_LEGACY_BM_FEES(cls):
        # The opReturn data used by legacy BM for burning BTC received from BTC trade fees.
        # For regtest testing burn bsq and use the pre-image `fee` which has the hash b3253b7b92bb7f0916b05f10d4fa92be8e48f5e6.
        # The opReturn data gets additionally prefixed with 1701
        return (
            {"1701b3253b7b92bb7f0916b05f10d4fa92be8e48f5e6"}
            if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest()
            else {
                "1701721206fe6b40777763de1c741f4fd2706d94775d",
            }
        )

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        cycles_in_dao_state_service: "CyclesInDaoStateService",
        my_proposal_list_service: "MyProposalListService",
        bsq_wallet_service: "BsqWalletService",
        burning_man_service: "BurningManService",
        burn_target_service: "BurnTargetService",
    ):
        self._dao_state_service = dao_state_service
        self._cycles_in_dao_state_service = cycles_in_dao_state_service
        self._my_proposal_list_service = my_proposal_list_service
        self._bsq_wallet_service = bsq_wallet_service
        self._burning_man_service = burning_man_service
        self._burn_target_service = burn_target_service

        self._current_chain_height: int = 0
        self._burn_target: Optional[int] = None
        self._burning_man_candidates_by_name: dict[str, "BurningManCandidate"] = {}
        self._accumulated_decayed_burned_amount: Optional[int] = None
        self._reimbursements: set["ReimbursementModel"] = set()
        self._average_distribution_per_cycle: Optional[int] = None
        self._my_compensation_request_names: Optional[set[str]] = None
        self._my_genesis_output_names: Optional[set[str]] = None
        self._legacy_burning_man_dpt: Optional["LegacyBurningMan"] = None
        self._legacy_burning_man_btc_fees: Optional["LegacyBurningMan"] = None
        self._proof_of_burn_op_return_tx_output_by_hash: dict[
            "StorageByteArray", set["TxOutput"]
        ] = {}
        self._burning_man_name_by_address: dict[str, str] = {}

        self._dao_state_service.add_dao_state_listener(self)
        last_block = self._dao_state_service.last_block
        if last_block:
            self._apply_block(last_block)

    def shut_down(self):
        self._dao_state_service.remove_dao_state_listener(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self._apply_block(block)

    def _apply_block(self, block: "Block"):
        self._current_chain_height = block.height
        self._burning_man_candidates_by_name.clear()
        self._reimbursements.clear()
        self._burn_target = None
        self._accumulated_decayed_burned_amount = None
        self._my_compensation_request_names = None
        self._average_distribution_per_cycle = None
        self._legacy_burning_man_dpt = None
        self._legacy_burning_man_btc_fees = None
        self._proof_of_burn_op_return_tx_output_by_hash.clear()
        self._burning_man_name_by_address.clear()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_burn_target(self) -> int:
        if self._burn_target is not None:
            return self._burn_target

        self._burn_target = self._burn_target_service.get_burn_target(
            self._current_chain_height,
            self.get_burning_man_candidates_by_name().values(),
        )
        return self._burn_target

    def get_boosted_burn_target(self) -> int:
        return (
            self.get_burn_target()
            + BurningManPresentationService.BURN_TARGET_BOOST_AMOUNT
        )

    def get_average_distribution_per_cycle(self) -> int:
        if self._average_distribution_per_cycle is not None:
            return self._average_distribution_per_cycle

        self._average_distribution_per_cycle = (
            self._burn_target_service.get_average_distribution_per_cycle(
                self._current_chain_height
            )
        )
        return self._average_distribution_per_cycle

    def get_expected_revenue(self, burning_man_candidate: "BurningManCandidate") -> int:
        return round(
            burning_man_candidate.capped_burn_amount_share
            * self.get_average_distribution_per_cycle()
        )

    # Left side in tuple is the amount to burn to reach the max. burn share based on the total burned amount.
    # This value is safe to not burn more than needed and to avoid to get capped.
    # The right side is the amount to burn to reach the max. burn share based on the boosted burn target.
    # This can lead to burning too much and getting capped.
    def get_candidate_burn_target(
        self, burning_man_candidate: "BurningManCandidate"
    ) -> tuple[int, int]:
        burn_target = self.get_burn_target()
        boosted_burn_target = (
            burn_target + BurningManPresentationService.BURN_TARGET_BOOST_AMOUNT
        )
        compensation_share = burning_man_candidate.compensation_share

        if boosted_burn_target <= 0 or compensation_share == 0:
            return (0, 0)

        max_compensation_share = min(
            BurningManService.MAX_BURN_SHARE, compensation_share
        )
        lower_base_target = round(burn_target * max_compensation_share)
        max_boosted_compensation_share = (
            burning_man_candidate.get_max_boosted_compensation_share()
        )
        upper_base_target = round(boosted_burn_target * max_boosted_compensation_share)
        total_burned_amount = self._get_accumulated_decayed_burned_amount()

        if total_burned_amount == 0:
            # The first BM would reach their max burn share by 5.46 BSQ already. But we suggest the lowerBaseTarget
            # as lower target to speed up the bootstrapping.
            return (lower_base_target, upper_base_target)

        if (
            burning_man_candidate.adjusted_burn_amount_share
            < max_boosted_compensation_share
        ):
            candidates_burn_amount = (
                burning_man_candidate.accumulated_decayed_burn_amount
            )
            # JAVA TODO We do not consider adjustedBurnAmountShare. This could lead to slight over burn. Atm we ignore that.
            my_burn_amount = (
                BurningManPresentationService.get_missing_amount_to_reach_target_share(
                    total_burned_amount,
                    candidates_burn_amount,
                    max_boosted_compensation_share,
                )
            )
            # If below dust we set value to 0
            my_burn_amount = 0 if my_burn_amount < 546 else my_burn_amount

            # In case the myBurnAmount would be larger than the upperBaseTarget we use the upperBaseTarget.
            my_burn_amount = min(my_burn_amount, upper_base_target)
            return (my_burn_amount, upper_base_target)
        else:
            # We have reached our cap.
            return (0, upper_base_target)

    @staticmethod
    def get_missing_amount_to_reach_target_share(
        total_burned_amount: int, my_burn_amount: int, my_target_share: float
    ) -> int:
        others = total_burned_amount - my_burn_amount
        share_target_others = 1 - my_target_share
        target_amount = (
            my_target_share / share_target_others * others
            if share_target_others > 0
            else 0
        )
        return round(target_amount) - my_burn_amount

    def get_reimbursements(self) -> set["ReimbursementModel"]:
        if self._reimbursements:
            return self._reimbursements

        self._reimbursements.update(
            self._burn_target_service.get_reimbursements(self._current_chain_height)
        )
        return self._reimbursements

    def find_my_genesis_output_names(self) -> Optional[set[str]]:
        if self._my_genesis_output_names is not None:
            return self._my_genesis_output_names

        genesis_tx = self._dao_state_service.get_genesis_tx()
        if genesis_tx:
            genesis_transaction: Optional["Transaction"] = (
                self._bsq_wallet_service.get_transaction(genesis_tx.id)
            )
            if genesis_transaction:
                self._my_genesis_output_names = {
                    f"{BurningManService.GENESIS_OUTPUT_PREFIX}{output.index}"
                    for output in genesis_transaction.outputs
                    if output.is_for_wallet(self._bsq_wallet_service.wallet)
                }
        if self._my_genesis_output_names is None:
            self._my_genesis_output_names = set()
        return self._my_genesis_output_names

    def get_my_compensation_request_names(self) -> Optional[set[str]]:
        # Can be empty, so we compare with null and reset to null at new block
        if self._my_compensation_request_names is not None:
            return self._my_compensation_request_names

        self._my_compensation_request_names = {
            proposal.name
            for proposal in self._my_proposal_list_service.list
            if isinstance(proposal, CompensationProposal)
        }
        return self._my_compensation_request_names

    def get_burning_man_candidates_by_name(self) -> dict[str, "BurningManCandidate"]:
        # Cached value is only used for currentChainHeight
        if self._burning_man_candidates_by_name:
            return self._burning_man_candidates_by_name

        self._burning_man_candidates_by_name.update(
            self._burning_man_service.get_burning_man_candidates_by_name(
                self._current_chain_height
            )
        )
        return self._burning_man_candidates_by_name

    def get_legacy_burning_man_for_dpt(self) -> Optional["LegacyBurningMan"]:
        if self._legacy_burning_man_dpt is not None:
            return self._legacy_burning_man_dpt

        # We do not add the legacy burningman to the list but keep it as class field only to avoid that it
        # interferes with usage of the burningManCandidatesByName map.
        self._legacy_burning_man_dpt = self._get_legacy_burning_man(
            self._burning_man_service.get_legacy_burning_man_address(
                self._current_chain_height
            ),
            BurningManPresentationService.OP_RETURN_DATA_LEGACY_BM_DPT,
        )
        return self._legacy_burning_man_dpt

    def get_legacy_burning_man_for_btc_fees(self) -> Optional["LegacyBurningMan"]:
        if self._legacy_burning_man_btc_fees is not None:
            return self._legacy_burning_man_btc_fees

        # We do not add the legacy burningman to the list but keep it as class field only to avoid that it
        # interferes with usage of the burning_man_candidates_by_name map.
        self._legacy_burning_man_btc_fees = self._get_legacy_burning_man(
            BurningManPresentationService.LEGACY_BURNING_MAN_BTC_FEES_ADDRESS,
            BurningManPresentationService.OP_RETURN_DATA_LEGACY_BM_FEES,
        )
        return self._legacy_burning_man_btc_fees

    def _get_legacy_burning_man(
        self, address: str, op_return_data: set[str]
    ) -> Optional["LegacyBurningMan"]:
        legacy_burning_man = LegacyBurningMan(address)
        #  The opReturnData used by legacy BM at burning BSQ.
        for (
            tx_outputs
        ) in self._get_proof_of_burn_op_return_tx_output_by_hash().values():
            for tx_output in tx_outputs:
                op_return_as_hex = tx_output.op_return_data.hex()
                if op_return_as_hex in op_return_data:
                    burn_output_height = tx_output.block_height
                    optional_tx = self._dao_state_service.get_tx(tx_output.tx_id)
                    burn_output_amount = optional_tx.burnt_bsq if optional_tx else 0
                    date = optional_tx.time if optional_tx else 0
                    cycle_index = self._cycles_in_dao_state_service.get_cycle_index_at_chain_height(
                        burn_output_height
                    )
                    legacy_burning_man.add_burn_output_model(
                        BurnOutputModel(
                            burn_output_amount,
                            burn_output_amount,
                            burn_output_height,
                            tx_output.tx_id,
                            date,
                            cycle_index,
                        )
                    )
        # Set remaining share if the sum of all capped shares does not reach 100%.
        burn_amount_share_of_others = sum(
            candidate.capped_burn_amount_share
            for candidate in self.get_burning_man_candidates_by_name().values()
        )
        legacy_burning_man.apply_burn_amount_share(1 - burn_amount_share_of_others)
        return legacy_burning_man

    def get_burning_man_name_by_address(self) -> dict[str, str]:
        if self._burning_man_name_by_address:
            return self._burning_man_name_by_address

        burning_man_candidates_by_name = (
            # copy to not alter source map. We do not store legacy BM in the source map.
            self.get_burning_man_candidates_by_name().copy()
        )
        burning_man_candidates_by_name[
            BurningManPresentationService.LEGACY_BURNING_MAN_DPT_NAME
        ] = self.get_legacy_burning_man_for_dpt()
        burning_man_candidates_by_name[
            BurningManPresentationService.LEGACY_BURNING_MAN_BTC_FEES_NAME
        ] = self.get_legacy_burning_man_for_btc_fees()

        receiver_addresses_by_burning_man_name: dict[str, set[str]] = {}
        for name, burning_man_candidate in burning_man_candidates_by_name.items():
            if name not in receiver_addresses_by_burning_man_name:
                receiver_addresses_by_burning_man_name[name] = set()
            receiver_addresses_by_burning_man_name[name].update(
                burning_man_candidate.get_all_addresses()
            )

        map: dict[str, str] = {}
        for name, addresses in receiver_addresses_by_burning_man_name.items():
            for address in addresses:
                map.setdefault(address, name)

        self._burning_man_name_by_address.update(map)
        return self._burning_man_name_by_address

    def get_total_amount_of_burned_bsq(self) -> int:
        return sum(
            candidate.accumulated_burn_amount
            for candidate in self.get_burning_man_candidates_by_name().values()
        )

    def get_bsq_burned_by_month(self, date_filter: datetime) -> int:
        default_zero_burn = {BurnOutputModel(0, 0, 0, "", 0, 0)}
        burning_men = self.get_burning_man_candidates_by_name()
        return sum(
            sum(
                burn_output.amount
                for burn_output in burning_man.burn_output_models_by_month.get(
                    date_filter, default_zero_burn
                )
            )
            for burning_man in burning_men.values()
        )

    @property
    def genesis_tx_id(self):
        return self._dao_state_service.genesis_tx_id

    def _get_proof_of_burn_op_return_tx_output_by_hash(
        self,
    ) -> dict["StorageByteArray", set["TxOutput"]]:
        if self._proof_of_burn_op_return_tx_output_by_hash:
            return self._proof_of_burn_op_return_tx_output_by_hash

        self._proof_of_burn_op_return_tx_output_by_hash.update(
            self._burning_man_service.get_proof_of_burn_op_return_tx_output_by_hash(
                self._current_chain_height
            )
        )
        return self._proof_of_burn_op_return_tx_output_by_hash

    def _get_accumulated_decayed_burned_amount(self) -> int:
        if self._accumulated_decayed_burned_amount is None:
            burning_man_candidates = self.get_burning_man_candidates_by_name().values()
            self._accumulated_decayed_burned_amount = (
                self._burn_target_service.get_accumulated_decayed_burned_amount(
                    burning_man_candidates, self._current_chain_height
                )
            )
        return self._accumulated_decayed_burned_amount
