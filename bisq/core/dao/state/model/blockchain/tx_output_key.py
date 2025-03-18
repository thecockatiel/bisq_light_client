from dataclasses import dataclass
from functools import total_ordering
from typing import Any

from utils.java_compat import java_string_compare, java_string_hashcode


@total_ordering
@dataclass(frozen=True)
class TxOutputKey:
    """
    Convenience object for identifying a TxOutput.
    Used as key in maps in the daoState.
    """

    tx_id: str
    index: int

    def __str__(self) -> str:
        return f"{self.tx_id}:{self.index}"

    @staticmethod
    def get_key_from_string(key_as_string: str) -> "TxOutputKey":
        """Creates a TxOutputKey from a string representation."""
        tokens = key_as_string.split(":")
        return TxOutputKey(tokens[0], int(tokens[1]))

    def __lt__(self, other: Any) -> bool:
        """Implements comparison for sorting."""
        if not isinstance(other, TxOutputKey):
            return NotImplemented
        return java_string_compare(str(self), str(other)) < 0

    def __eq__(self, other: Any) -> bool:
        """Implements equality comparison."""
        if not isinstance(other, TxOutputKey):
            return NotImplemented
        return java_string_compare(str(self), str(other)) == 0

    def __hash__(self):
        result = (59 + self.index) * 59
        if self.tx_id is None:
            result += 43
        else:
            result += java_string_hashcode(self.tx_id)
        return result
