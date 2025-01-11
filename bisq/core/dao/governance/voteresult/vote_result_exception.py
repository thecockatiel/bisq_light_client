from bisq.core.dao.state.model.governance.cycle import Cycle

# TODO
class VoteResultException(Exception):
    def __init__(self, cycle: Cycle, cause: Exception = None):
        super().__init__(cause)
        self.height_of_first_block_in_cycle = cycle.height_of_first_block

    def __str__(self):
        return (
            f"VoteResultException{{\n"
            f"     heightOfFirstBlockInCycle={self.height_of_first_block_in_cycle}\n"
            f"}} {super().__str__()}"
        )
