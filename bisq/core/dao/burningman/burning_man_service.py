from typing import TYPE_CHECKING

from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate


if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService


# TODO: implement if necessary
class BurningManService:
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

    def __init__(self, dao_state_service: "DaoStateService") -> None:
        self.dao_state_service = dao_state_service

    def get_legacy_burning_man_address(self, chain_height: int) -> str:
        return self.dao_state_service.get_param_value(
            Param.RECIPIENT_BTC_ADDRESS, chain_height
        )

    def get_active_burning_man_candidates(
        self,
        chain_height: int,
        limit_capping_rounds: bool = None,
    ) -> set["BurningManCandidate"]:
        from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
            DelayedPayoutTxReceiverService,
        )

        if limit_capping_rounds is None:
            limit_capping_rounds = (
                not DelayedPayoutTxReceiverService.is_proposal_412_activated()
            )

        raise NotImplementedError(
            "BurningManService.get_active_burning_man_candidates Not implemented yet"
        )

    def get_active_burning_man_candidates_by_name(
        self,
        chain_height: int,
        limit_capping_rounds: bool = None,
    ) -> dict[str, "BurningManCandidate"]:
        from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
            DelayedPayoutTxReceiverService,
        )

        if limit_capping_rounds is None:
            limit_capping_rounds = (
                not DelayedPayoutTxReceiverService.is_proposal_412_activated()
            )

        raise NotImplementedError(
            "BurningManService.get_active_burning_man_candidates_by_name Not implemented yet"
        )

    def get_burning_man_candidates_by_name(
        chain_height: int, limit_capping_rounds: bool = None
    ) -> dict[str, "BurningManCandidate"]:
        from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
            DelayedPayoutTxReceiverService,
        )

        if limit_capping_rounds is None:
            limit_capping_rounds = (
                not DelayedPayoutTxReceiverService.is_proposal_412_activated()
            )

        raise NotImplementedError(
            "BurningManService.get_burning_man_candidates_by_name Not implemented yet"
        )
