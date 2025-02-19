from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService


@dataclass(frozen=True)
class FeePayment:
    tx_id: str
    fee: int

    def days_covered_by_fee(self, bsq_fee_per_day: int) -> int:
        return self.fee // bsq_fee_per_day if bsq_fee_per_day > 0 else 0

    def get_passed_days(self, dao_state_service: "DaoStateService") -> Optional[int]:
        tx = dao_state_service.get_tx(self.tx_id)
        if tx:
            passed_blocks = dao_state_service.chain_height - tx.block_height
            return passed_blocks // 144
        else:
            return None

    def __str__(self) -> str:
        return (
            f"FeePayment{{\n"
            f"     tx_id='{self.tx_id}',\n"
            f"     fee={self.fee}\n"
            f"}}"
        )
