from dataclasses import dataclass

from bisq.core.dao.state.model.blockchain.script_type import ScriptType


@dataclass(frozen=True)
class TempAccountingTxOutput:
    value: int
    address: str
    script_type: ScriptType
