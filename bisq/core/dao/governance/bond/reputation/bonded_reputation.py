from typing import TYPE_CHECKING
from bisq.core.dao.governance.bond.bond import Bond

if TYPE_CHECKING:
    from bisq.core.dao.governance.bond.reputation.reputation import Reputation


class BondedReputation(Bond["Reputation"]):
    """Wrapper for reputation which contains the mutable state of a bonded reputation. Only kept in memory."""

    def __str__(self) -> str:
        return f"BondedReputation{{\n}} {super().__str__()}"
