from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from bisq.core.dao.governance.bond.bonded_asset import BondedAsset
from typing import Optional
from bisq.core.dao.governance.bond.bond_state import BondState

_T = TypeVar("T", bound="BondedAsset")


class Bond(Generic[_T], ABC):
    """Base class for BondedRole and BondedReputation. Holds the state of the bonded asset."""

    def __init__(self, bonded_asset: _T):
        self.bonded_asset: _T = bonded_asset
        self.lockup_tx_id: Optional[str] = None
        self.unlock_tx_id: Optional[str] = None
        self.bond_state: BondState = BondState.READY_FOR_LOCKUP
        self.amount: int = 0
        self.lockup_date: int = 0
        self.unlock_date: int = 0
        self.lock_time: int = 0

    @property
    def is_active(self) -> bool:
        return self.bond_state.is_active

    def __eq__(self, other):
        if not isinstance(other, Bond):
            return False
        return (
            self.amount == other.amount
            and self.lockup_date == other.lockup_date
            and self.unlock_date == other.unlock_date
            and self.lock_time == other.lock_time
            and self.bonded_asset == other.bonded_asset
            and self.lockup_tx_id == other.lockup_tx_id
            and self.unlock_tx_id == other.unlock_tx_id
            and self.bond_state.name == other.bond_state.name
        )

    def __hash__(self):
        return hash(
            (
                self.bonded_asset,
                self.lockup_tx_id,
                self.unlock_tx_id,
                self.bond_state.name,
                self.amount,
                self.lockup_date,
                self.unlock_date,
                self.lock_time,
            )
        )

    def __str__(self):
        return (
            f"Bond{{\n"
            f"     bonded_asset={self.bonded_asset},\n"
            f"     lockup_tx_id='{self.lockup_tx_id}',\n"
            f"     unlock_tx_id='{self.unlock_tx_id}',\n"
            f"     bond_state={self.bond_state},\n"
            f"     amount={self.amount},\n"
            f"     lockup_date={self.lockup_date},\n"
            f"     unlock_date={self.unlock_date},\n"
            f"     lock_time={self.lock_time}\n"
            f"}}"
        )
