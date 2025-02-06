from enum import IntEnum, auto

from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.string_column import StringColumn
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


class ZippedStringColumns:
    """
    For zipping multiple StringColumns into a single StringColumn.
    Useful for displaying amount and volume range values.
    """

    class DUPLICATION_MODE(IntEnum):
        EXCLUDE_DUPLICATES = auto()
        INCLUDE_DUPLICATES = auto()

    def __init__(
        self,
        name: str,
        justification: ColumnJustification,
        delimiter: str,
        *columns: StringColumn
    ):
        self.name = name
        self.justification = justification
        self.delimiter = delimiter
        self.columns = columns
        self._validate_column_data()

    def as_string_column(self, duplication_mode: "DUPLICATION_MODE") -> StringColumn:
        string_column = StringColumn(self.name, self.justification)

        self._build_rows(string_column, duplication_mode)

        # Re-set the column name field to its justified value, in case any of the column
        # values are longer than the name passed to this constructor.
        string_column.name = string_column.to_justified_string(self.name)

        return string_column

    def _build_rows(
        self, string_column: StringColumn, duplication_mode: "DUPLICATION_MODE"
    ):
        # Populate the StringColumn with unjustified zipped values;  we cannot justify
        # the zipped values until stringColumn knows its final maxWidth.
        for row_index in range(self.columns[0].row_count):
            row = self._build_row(row_index, duplication_mode)
            string_column.add_row(row)

        self._format_rows(string_column)

    def _build_row(self, row_index: int, duplication_mode: "DUPLICATION_MODE") -> str:
        row_builder = []
        processed_values = (
            []
            if duplication_mode
            == ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
            else None
        )

        for col_index in range(len(self.columns)):
            value = self.columns[col_index].rows[row_index]
            if (
                duplication_mode
                == ZippedStringColumns.DUPLICATION_MODE.INCLUDE_DUPLICATES
            ):
                if row_builder:
                    row_builder.append(self.delimiter)

                row_builder.append(value)
            elif value not in processed_values:
                if row_builder:
                    row_builder.append(self.delimiter)

                row_builder.append(value)
                processed_values.append(value)

        return "".join(row_builder)

    def _format_rows(self, string_column: StringColumn):
        # Now we can justify the zipped string values in the new StringColumn.
        for row_index in range(string_column.row_count):
            unjustified = string_column.get_row(row_index)
            justified = string_column.to_justified_string(unjustified)
            string_column.update_row(row_index, justified)

    def _validate_column_data(self):
        if not self.columns:
            raise IllegalStateException(
                "Cannot zip columns because they do not have any data"
            )

        first_column = self.columns[0]
        if first_column.is_empty:
            raise IllegalStateException("1st column has no data")

        for col_index in range(1, len(self.columns)):
            if len(self.columns[col_index].row_count) != first_column.row_count:
                raise IllegalStateException(
                    "Columns do not have the same number of rows"
                )
