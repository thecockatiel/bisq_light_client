from dataclasses import dataclass


@dataclass(frozen=True)
class TempAccountingTxInput:
    sequence: int
    tx_in_witness: tuple[str]
