from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate


class LegacyBurningMan(BurningManCandidate):

    def __init__(self, address: str):
        super().__init__()
        self.receiver_address = self.most_recent_address = address

    def apply_burn_amount_share(self, burn_amount_share: float):
        self.burn_amount_share = burn_amount_share

        # We do not adjust burn_amount_share for legacy BM from capped BM
        self.adjusted_burn_amount_share = burn_amount_share

        # We do not cap burn_amount_share for legacy BM
        self.capped_burn_amount_share = burn_amount_share

    def calculate_shares(
        self,
        total_decayed_compensation_amounts: float,
        total_decayed_burn_amounts: float,
    ):
        # do nothing
        pass

    def impose_cap(self, capping_round: int, adjusted_burn_amount_share: float):
        # do nothing
        pass

    def calculate_capped_and_adjusted_shares(
        self,
        sum_all_capped_burn_amount_shares: float,
        sum_all_non_capped_burn_amount_shares: float,
        num_applied_capping_rounds: int,
    ):
        # do nothing
        pass

    def get_all_addresses(self) -> set[str]:
        addr = self.get_receiver_address()
        if addr:
            return {addr}
        return set()
