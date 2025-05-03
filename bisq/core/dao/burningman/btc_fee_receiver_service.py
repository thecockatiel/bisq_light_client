from typing import TYPE_CHECKING
from bisq.core.dao.state.dao_state_listener import DaoStateListener
import random

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.burningman.burning_man_service import BurningManService
    from bisq.core.dao.state.dao_state_service import DaoStateService


class BtcFeeReceiverService(DaoStateListener):

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        burning_man_service: "BurningManService",
    ):
        self._dao_state_service = dao_state_service
        self._burning_man_service = burning_man_service
        self._current_chain_height = 0

        self._dao_state_service.add_dao_state_listener(self)
        last_block = dao_state_service.last_block
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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_address(self) -> str:
        active_burning_man_candidates = (
            self._burning_man_service.get_active_burning_man_candidates(
                self._current_chain_height
            )
        )
        if not active_burning_man_candidates:
            # If there are no compensation requests (e.g. at dev testing) we fall back to the default address
            return self._burning_man_service.get_legacy_burning_man_address(
                self._current_chain_height
            )

        # It might be that we do not reach 100% if some entries had a cappedBurnAmountShare.
        # In that case we fill up the gap to 100% with the legacy BM.
        # cappedBurnAmountShare is a % value represented as float. Smallest supported value is 0.01% -> 0.0001.
        # By multiplying it with 10000 and using math.floor we limit the candidate to 0.01%.
        # Entries with 0 will be ignored in the selection method, so we do not need to filter them out.
        ceiling = 10000
        amount_list = [
            int(capped_burn_amount_share * ceiling)
            for capped_burn_amount_share in (
                candidate.capped_burn_amount_share
                for candidate in active_burning_man_candidates
            )
        ]
        total_amount = sum(amount_list)
        # If we have not reached the 100% we fill the missing gap with the legacy BM
        if total_amount < ceiling:
            amount_list.append(ceiling - total_amount)

        winner_index = BtcFeeReceiverService.get_random_index(amount_list)
        if winner_index == len(active_burning_man_candidates):
            # If we have filled up the missing gap to 100% with the legacy BM we would get an index out of bounds of
            # the burningManCandidates as we added for the legacy BM an entry at the end.
            return self._burning_man_service.get_legacy_burning_man_address(
                self._current_chain_height
            )
        return active_burning_man_candidates[
            winner_index
        ].receiver_address or self._burning_man_service.get_legacy_burning_man_address(
            self._current_chain_height
        )

    @staticmethod
    def get_random_index(weights: list[int]) -> int:
        total_weight = sum(weights)
        if total_weight == 0:
            return -1
        target = random.randint(1, total_weight)
        return BtcFeeReceiverService.find_index(weights, target)

    @staticmethod
    def find_index(weights: list[int], target: int) -> int:
        current_range = 0
        for i, weight in enumerate(weights):
            current_range += weight
            if current_range >= target:
                return i
        return 0
