from bisq.cli.table.column.abstract_column import AbstractColumn
from bisq.cli.table.column.column_justification import ColumnJustification


class BooleanColumn(AbstractColumn["BooleanColumn", bool]):
    DEFAULT_TRUE_AS_STRING = "YES"
    DEFAULT_FALSE_AS_STRING = "NO"

    def __init__(
        self,
        name: str,
        justification: ColumnJustification = None,
        true_as_string: str = None,
        false_as_string: str = None,
    ):
        if justification is None:
            justification = ColumnJustification.LEFT
        super().__init__(name, justification)
        self._rows: list[bool] = []
        self.max_width: int = len(name)
        self.true_as_string = true_as_string or BooleanColumn.DEFAULT_TRUE_AS_STRING
        self.false_as_string = false_as_string or BooleanColumn.DEFAULT_FALSE_AS_STRING

    def is_new_max_width(self, s: str) -> bool:
        return s is not None and s != "" and len(s) > self.max_width

    def add_row(self, row: bool):
        self.rows.append(row)

        s = self._as_string(row)
        self.string_column.add_row(s)
        if self.is_new_max_width(s):
            self.max_width = len(s)

    @property
    def rows(self) -> list[bool]:
        return self._rows

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def is_empty(self) -> bool:
        return not self.rows

    def get_row(self, row_index: int):
        return self.rows[row_index]

    def update_row(self, row_index: int, new_value: bool):
        self.rows[row_index] = new_value

    def get_row_as_formatted_string(self, row_index: int):
        return self.to_justified_string(str(self.get_row(row_index)))

    def as_string_column(self):
        for row_index in range(self.row_count):
            unjustified = self.string_column.get_row(row_index)
            justified = self.string_column.to_justified_string(unjustified)
            self.string_column.update_row(row_index, justified)

        return self.string_column

    def _as_string(self, val: bool):
        return self.true_as_string if val else self.false_as_string
