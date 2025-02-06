from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.number_column import NumberColumn


class LongColumn(NumberColumn["LongColumn", int]):
    def __init__(self, name: str, justification: ColumnJustification = None):
        if justification is None:
            justification = ColumnJustification.RIGHT
        super().__init__(name, justification)
        self._rows: list[int] = []
        self.max_width: int = len(name)

    def is_new_max_width(self, s: str) -> bool:
        return s is not None and s != "" and len(s) > self.max_width

    def add_row(self, row: int):
        self.rows.append(row)

        s = str(row)
        if self.is_new_max_width(s):
            self.max_width = len(s)

    @property
    def rows(self) -> list[int]:
        return self._rows

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def is_empty(self) -> bool:
        return not self.rows

    def get_row(self, row_index: int):
        return self.rows[row_index]

    def update_row(self, row_index: int, new_value: int):
        self.rows[row_index] = new_value

    def get_row_as_formatted_string(self, row_index: int):
        return self.to_justified_string(str(self.get_row(row_index)))

    def as_string_column(self):
        for row_index in range(self.row_count):
            self.string_column.add_row(self.get_row_as_formatted_string(row_index))

        return self.string_column
