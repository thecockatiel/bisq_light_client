from typing import TYPE_CHECKING, Generic, TypeVar
from bisq.cli.table.column.abstract_column import AbstractColumn
from bisq.cli.table.column.column_justification import ColumnJustification

_T = TypeVar("_T")


class StringColumn(AbstractColumn["StringColumn", str]):

    def __init__(self, name: str, justification: ColumnJustification = None):
        if justification is None:
            justification = ColumnJustification.LEFT
        super().__init__(name, justification)
        self._rows: list[str] = []
        self.max_width: int = len(name)

    def is_new_max_width(self, s: str) -> bool:
        return s is not None and s != "" and len(s) > self.max_width

    def add_row(self, row: str):
        self.rows.append(row)
        if self.is_new_max_width(row):
            self.max_width = len(row)

    @property
    def rows(self) -> list[str]:
        return self._rows

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def is_empty(self) -> bool:
        return not self.rows

    def get_row(self, row_index: int):
        return self.rows[row_index]

    def update_row(self, row_index: int, new_value: str):
        self.rows[row_index] = new_value

    def get_row_as_formatted_string(self, row_index: int):
        return self.get_row(row_index)

    def as_string_column(self):
        return self

    def justify(self):
        if self.justification == ColumnJustification.RIGHT:
            for row_index in range(self.row_count):
                unjustified = self.get_row(row_index)
                justified = self.to_justified_string(unjustified)
                self.update_row(row_index, justified)
        return self
