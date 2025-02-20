from datetime import datetime
from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_logger
from bisq.common.util.date_util import DateUtil

if TYPE_CHECKING:
    from bisq.core.dao.burningman.model.burn_output_model import BurnOutputModel
    from bisq.core.dao.burningman.model.compensation_model import CompensationModel

logger = get_logger(__name__)


class BurningManCandidate:
    """
    Contains all relevant data for a burningman candidate (any contributor who has made a compensation request or was
    a receiver of a genesis output).
    """

    def __init__(self):
        self.compensation_models: set["CompensationModel"] = set()
        self.accumulated_compensation_amount: int = 0
        self.accumulated_decayed_compensation_amount: int = 0
        self.compensation_share: float = (
            0.0  #  Share of accumulated decayed compensation amounts in relation to total issued amounts
        )

        self.receiver_address: Optional[str] = None

        # For deploying a bugfix with mostRecentAddress we need to maintain the old version to avoid breaking the
        # trade protocol. We use the legacyMostRecentAddress until the activation date where we
        # enforce the version by the filter to ensure users have updated.
        # See: https://github.com/bisq-network/bisq/issues/6699
        self.most_recent_address: Optional[str] = None  # exclude from equal and hash

        self.burn_output_models: set["BurnOutputModel"] = set()
        self.burn_output_models_by_month: dict[datetime, set["BurnOutputModel"]] = {}
        self.accumulated_burn_amount: int = 0
        self.accumulated_decayed_burn_amount: int = 0
        # Share of accumulated decayed burn amounts in relation to total burned amounts
        self.burn_amount_share: float = 0.0
        # Capped burnAmountShare. Cannot be larger than boostedCompensationShare
        self.capped_burn_amount_share: float = 0.0
        # The burnAmountShare adjusted in case there are cappedBurnAmountShare.
        # We redistribute the over-burned amounts to the group of not capped candidates.
        self.adjusted_burn_amount_share: float = 0.0
        self.round_capped: Optional[int] = None

    def get_receiver_address(
        self, is_bugfix_6699_activated: bool = None
    ) -> Optional[str]:
        if is_bugfix_6699_activated is None:
            # TODO: we can probably replace it by True since It's been long since activation
            from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
                DelayedPayoutTxReceiverService,
            )

            is_bugfix_6699_activated = (
                DelayedPayoutTxReceiverService.is_bugfix_6699_activated()
            )

        if is_bugfix_6699_activated:
            return self.receiver_address
        else:
            return self.most_recent_address

    def add_burn_output_model(self, burn_output_model: "BurnOutputModel"):
        if burn_output_model in self.burn_output_models:
            return
        self.burn_output_models.add(burn_output_model)

        month = DateUtil.get_start_of_month(
            datetime.fromtimestamp(burn_output_model.date / 1000)
        )
        if month not in self.burn_output_models_by_month:
            self.burn_output_models_by_month[month] = set()
        self.burn_output_models_by_month[month].add(burn_output_model)

        self.accumulated_decayed_burn_amount += burn_output_model.decayed_amount
        self.accumulated_burn_amount += burn_output_model.amount

    def add_compensation_model(self, compensation_model: "CompensationModel"):
        if compensation_model in self.compensation_models:
            return

        self.compensation_models.add(compensation_model)

        self.accumulated_decayed_compensation_amount += (
            compensation_model.decayed_amount
        )
        self.accumulated_compensation_amount += compensation_model.amount

        has_any_custom_address = any(
            model.is_custom_address for model in self.compensation_models
        )
        if has_any_custom_address:
            # If any custom address was defined, we only consider custom addresses and sort them to take the
            # most recent one.
            self.receiver_address = max(
                (
                    model
                    for model in self.compensation_models
                    if model.is_custom_address
                ),
                key=lambda model: model.height,
            ).address
        else:
            # If no custom addresses ever have been defined, we take the change address of the compensation request
            # and use the earliest address. This helps to avoid change of address with every new comp. request.
            self.receiver_address = min(
                self.compensation_models, key=lambda model: model.height
            ).address

        # For backward compatibility reasons we need to maintain the old buggy version.
        # See: https://github.com/bisq-network/bisq/issues/6699.
        self.most_recent_address = max(
            self.compensation_models, key=lambda model: model.height
        ).address

    def get_all_addresses(self) -> set[str]:
        return {model.address for model in self.compensation_models}

    def calculate_shares(
        self,
        total_decayed_compensation_amounts: float,
        total_decayed_burn_amounts: float,
    ):
        self.compensation_share = (
            self.accumulated_decayed_compensation_amount
            / total_decayed_compensation_amounts
            if total_decayed_compensation_amounts > 0
            else 0
        )
        self.burn_amount_share = (
            self.accumulated_decayed_burn_amount / total_decayed_burn_amounts
            if total_decayed_burn_amounts > 0
            else 0
        )

    def impose_cap(self, capping_round: int, adjusted_burn_amount_share: float):
        self.round_capped = capping_round
        # NOTE: The adjusted burn share set here will not affect the final capped burn share, only
        # the presentation service, so we need not worry about rounding errors affecting consensus.
        self.adjusted_burn_amount_share = adjusted_burn_amount_share

    def calculate_capped_and_adjusted_shares(
        self,
        sum_all_capped_burn_amount_shares: float,
        sum_all_non_capped_burn_amount_shares: float,
        num_applied_capping_rounds: int,
    ):
        max_boosted_compensation_share = self.get_max_boosted_compensation_share()
        if self.round_capped is None:
            self.adjusted_burn_amount_share = self.burn_amount_share
            if sum_all_capped_burn_amount_shares == 0:
                # If no one is capped we do not need to do any adjustment
                self.capped_burn_amount_share = self.burn_amount_share
            else:
                # The difference of the cappedBurnAmountShare and burnAmountShare will get redistributed to all
                # non-capped candidates.
                distribution_base = 1 - sum_all_capped_burn_amount_shares
                if sum_all_non_capped_burn_amount_shares == 0:
                    # In case we get sumAllNonCappedBurnAmountShares our burnAmountShare is also 0.
                    self.capped_burn_amount_share = self.burn_amount_share
                else:
                    adjustment = (
                        distribution_base / sum_all_non_capped_burn_amount_shares
                    )
                    self.adjusted_burn_amount_share = (
                        self.burn_amount_share * adjustment
                    )
                    if self.adjusted_burn_amount_share < max_boosted_compensation_share:
                        self.capped_burn_amount_share = self.adjusted_burn_amount_share
                    else:
                        #  We exceeded the cap by the adjustment. This will lead to the legacy BM getting the
                        #  difference of the adjusted amount and the maxBoostedCompensationShare.
                        #  NOTE: When the number of capping rounds are unlimited (that is post- Proposal 412
                        #   activation), we should only get to this branch as a result of floating point rounding
                        #   errors. In that case, the extra amount the LBM gets is negligible.
                        self.capped_burn_amount_share = max_boosted_compensation_share
                        self.round_capped = num_applied_capping_rounds
        else:
            self.capped_burn_amount_share = max_boosted_compensation_share

    def get_burn_cap_ratio(self) -> float:
        """
        NOTE: This is less than 1.0 precisely when burn_amount_share < max_boosted_compensation_share,
        in spite of any floating point rounding errors, since 1.0 is proportionately at least as
        close to the previous double as any two consecutive nonzero doubles on the number line.
        """
        return (
            self.burn_amount_share / self.get_max_boosted_compensation_share()
            if self.burn_amount_share > 0.0
            else 0.0
        )

    def get_max_boosted_compensation_share(self) -> float:
        from bisq.core.dao.burningman.burning_man_service import BurningManService
        return min(
            BurningManService.MAX_BURN_SHARE,
            self.compensation_share * BurningManService.ISSUANCE_BOOST_FACTOR,
        )

    def __str__(self) -> str:
        return (
            f"BurningManCandidate{{\n"
            f"    compensation_models={self.compensation_models},\n"
            f"    accumulated_compensation_amount={self.accumulated_compensation_amount},\n"
            f"    accumulated_decayed_compensation_amount={self.accumulated_decayed_compensation_amount},\n"
            f"    compensation_share={self.compensation_share},\n"
            f"    receiver_address={self.receiver_address},\n"
            f"    most_recent_address={self.most_recent_address},\n"
            f"    burn_output_models={self.burn_output_models},\n"
            f"    accumulated_burn_amount={self.accumulated_burn_amount},\n"
            f"    accumulated_decayed_burn_amount={self.accumulated_decayed_burn_amount},\n"
            f"    burn_amount_share={self.burn_amount_share},\n"
            f"    capped_burn_amount_share={self.capped_burn_amount_share},\n"
            f"    adjusted_burn_amount_share={self.adjusted_burn_amount_share},\n"
            f"    round_capped={self.round_capped}\n"
            f"}}"
        )

    def __eq__(self, other):
        if not isinstance(other, BurningManCandidate):
            return False
        return (
            self.compensation_models == other.compensation_models
            and self.accumulated_compensation_amount
            == other.accumulated_compensation_amount
            and self.accumulated_decayed_compensation_amount
            == other.accumulated_decayed_compensation_amount
            and self.compensation_share == other.compensation_share
            and self.receiver_address == other.receiver_address
            and self.burn_output_models == other.burn_output_models
            and self.accumulated_burn_amount == other.accumulated_burn_amount
            and self.accumulated_decayed_burn_amount
            == other.accumulated_decayed_burn_amount
            and self.burn_amount_share == other.burn_amount_share
            and self.capped_burn_amount_share == other.capped_burn_amount_share
            and self.adjusted_burn_amount_share == other.adjusted_burn_amount_share
            and self.round_capped == other.round_capped
        )

    def __hash__(self):
        return hash(
            (
                frozenset(self.compensation_models),
                frozenset(self.burn_output_models),
                self.accumulated_compensation_amount,
                self.accumulated_decayed_compensation_amount,
                self.compensation_share,
                self.receiver_address,
                self.accumulated_burn_amount,
                self.accumulated_decayed_burn_amount,
                self.burn_amount_share,
                self.capped_burn_amount_share,
                self.adjusted_burn_amount_share,
                self.round_capped,
            )
        )
