from typing import TYPE_CHECKING
from bisq.core.dao.governance.bond.bond import Bond

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.role import Role


class BondedRole(Bond["Role"]):
    """Wrapper for role which contains the mutable state of a bonded role. Only kept in memory."""

    def __str__(self):
        return f"BondedRole{{\n}} {super().__str__()}"
