from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.ballot import Ballot
    from bisq.core.dao.state.model.governance.cycle import Cycle


class VoteResultException(Exception):
    def __init__(self, cycle: "Cycle", cause: Exception = None):
        super().__init__(cause)
        self.height_of_first_block_in_cycle = cycle.height_of_first_block

    def __str__(self):
        return (
            f"VoteResultException{{\n"
            f"     heightOfFirstBlockInCycle={self.height_of_first_block_in_cycle}\n"
            f"}} {super().__str__()}"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Static sub classes
    # ///////////////////////////////////////////////////////////////////////////////////////////

    class ConsensusException(Exception):
        def __str__(self):
            return f"ConsensusException{{\n}} {super().__str__()}"

    class ValidationException(Exception):
        def __init__(self, cause=None):
            if isinstance(cause, Exception):
                super().__init__("Validation of vote result failed.", cause)
            super().__init__(cause)

        def __str__(self):
            return (
                f"ValidationException{{\n"
                f"     cause={self.args[1] if len(self.args) > 1 else None}\n"
                f"}} {super().__str__()}"
            )

    class MissingBallotException(Exception):
        def __init__(
            self,
            existing_ballots: list["Ballot"],
            proposal_tx_ids_of_missing_ballots: list[str],
        ):
            super().__init__(
                f"Missing ballots. proposalTxIdsOfMissingBallots={proposal_tx_ids_of_missing_ballots}"
            )
            self.existing_ballots = existing_ballots
            self.proposal_tx_ids_of_missing_ballots = proposal_tx_ids_of_missing_ballots

        def __str__(self):
            return (
                f"MissingBallotException{{\n"
                f"     existingBallots={self.existing_ballots},\n"
                f"     proposalTxIdsOfMissingBallots={self.proposal_tx_ids_of_missing_ballots}\n"
                f"}} {super().__str__()}"
            )

    class DecryptionException(Exception):

        def __str__(self):
            return f"DecryptionException{{\n}} {super().__str__()}"
