from dataclasses import dataclass


@dataclass(frozen=True)
class UtxoMismatch:
    height: int
    sum_utxo: int
    sum_bsq: int
