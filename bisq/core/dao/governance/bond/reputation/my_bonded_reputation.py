from typing import TYPE_CHECKING
from bisq.core.dao.governance.bond.bond import Bond

if TYPE_CHECKING:
    from bisq.core.dao.governance.bond.reputation.my_reputation import MyReputation


class MyBondedReputation(Bond["MyReputation"]):
    """
    Wrapper for reputation which contains the mutable state of my bonded reputation. Only kept in memory.
    As it carries MyReputation it has access to the private salt data.
    """

    def __str__(self) -> str:
        return f"MyBondedReputation{{\n}} {super().__str__()}"
