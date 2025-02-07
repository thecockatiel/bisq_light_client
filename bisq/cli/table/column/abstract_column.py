from abc import ABC
from typing import Generic, TypeVar
from bisq.cli.table.column.column import Column
from bisq.cli.table.column.column_justification import ColumnJustification

_T = TypeVar("_T")
_C = TypeVar("_C", bound=Column[_T])


class AbstractColumn(Generic[_C, _T], Column[_T], ABC):
    """Partial implementation of the Column interface."""

    def __init__(self, name: str, justification: ColumnJustification):
        # The name field is not final, so it can be re-set for column alignment
        self._name = name
        self._justification = justification

        # We create an encapsulated StringColumn up front to populate with formatted
        # strings in each this.addRow(Long value) call.  But we will not know how
        # to justify the cached, formatted string until the column is fully populated.
        from bisq.cli.table.column.string_column import StringColumn

        self.string_column = (
            None
            if isinstance(self, StringColumn)
            else StringColumn(name, justification)
        )
        # The max width is not known until after column is fully populated.
        self.max_width = 0

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def width(self) -> int:
        return self.max_width

    @property
    def justification(self) -> ColumnJustification:
        return self._justification

    def justify(self) -> Column[_T]:
        from bisq.cli.table.column.string_column import StringColumn

        if (
            isinstance(self, StringColumn)
            and self.justification == ColumnJustification.RIGHT
        ):
            return self.string_column.justify()
        else:
            return self  # no-op

    def to_justified_string(self, s: str) -> str:
        if self.justification == ColumnJustification.LEFT:
            return s.ljust(self.max_width)
        elif self.justification == ColumnJustification.RIGHT:
            return s.rjust(self.max_width)
        else:
            return s
