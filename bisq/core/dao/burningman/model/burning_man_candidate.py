from typing import Optional


# TODO
class BurningManCandidate:

    def __init__(self) -> None:
        self.receiver_address: Optional[str] = None

        # For deploying a bugfix with mostRecentAddress we need to maintain the old version to avoid breaking the
        # trade protocol. We use the legacyMostRecentAddress until the activation date where we
        # enforce the version by the filter to ensure users have updated.
        # See: https://github.com/bisq-network/bisq/issues/6699
        self.most_recent_address: Optional[str] = None

        self.capped_burn_amount_share = 0.0

    def get_receiver_address(
        self, is_bugfix_6699_activated: bool = None
    ) -> Optional[str]:
        if is_bugfix_6699_activated is None:
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
