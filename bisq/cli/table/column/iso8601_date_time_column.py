from datetime import datetime, timezone
from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.number_column import NumberColumn


class Iso8601DateTimeColumn(NumberColumn[int]):
    """For displaying (long) timestamp values as ISO-8601 dates in UTC time zone."""

    def __init__(self, name: str, justification: ColumnJustification = None):
        if justification is None:
            justification = ColumnJustification.LEFT
        super().__init__(name, justification)
        self.max_width: int = len(name)

    def get_row_as_formatted_string(self, row_index: int) -> str:
        time = self.get_row(row_index) # time is in ms
        iso_formatted = (
            datetime.fromtimestamp(time/1000)
            .isoformat(timespec="seconds")
            .rstrip("+00:00")
            .rstrip("Z")
            + "Z"
        )
        if self.justification == ColumnJustification.LEFT:
            return iso_formatted.ljust(self.max_width)
        else:
            return iso_formatted.rjust(self.max_width)

    def as_string_column(self):
        for row_index in range(self.row_count):
            self.string_column.add_row(self.get_row_as_formatted_string(row_index))

        return self.string_column
