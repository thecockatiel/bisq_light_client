from io import StringIO
import sys
from typing import TYPE_CHECKING, Iterable

from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


if TYPE_CHECKING:
    from bisq.cli.table.column.column import Column

    try:
        from _typeshed import SupportsWrite
    except:
        pass


class Table:
    """
    A simple table of formatted data for the CLI's output console.  A table must be
    created with at least one populated column, and each column passed to the constructor
    must contain the same number of rows.  Null checking is omitted because tables are
    populated by protobuf message fields which cannot be null.

    All data in a column has the same type: long, string, etc., but a table
    may contain an arbitrary number of columns of any type.  For output formatting
    purposes, numeric and date columns should be transformed to a StringColumn type with
    formatted and justified string values before being passed to the constructor.

    This is not a relational, rdbms table.
    """

    column_delimiter_length = 2

    def __init__(self, *columns: "Column"):
        self.columns = columns
        self.row_count = columns[0].row_count if columns else 0
        self._validate_structure()

    def print(self, file: "SupportsWrite[str]" = sys.stdout):
        self._print_column_names(file)
        for row_index in range(self.row_count):
            self._print_row(file, row_index)

    def _print_column_names(self, file: "SupportsWrite[str]"):
        for col_index, column in enumerate(self.columns):
            justified_name = (
                column.name.rjust(column.width)
                if column.justification == ColumnJustification.RIGHT
                else column.name
            )
            padded_width = (
                len(column.name)
                if col_index == len(self.columns) - 1
                else column.width + Table.column_delimiter_length
            )
            print(justified_name.ljust(padded_width), end='', file=file)
        print("", file=file)

    def _print_row(self, file: "SupportsWrite[str]", row_index: int):
        for col_index, column in enumerate(self.columns):
            padded_width = (
                column.width
                if col_index == len(self.columns) - 1
                else column.width + Table.column_delimiter_length
            )
            print(str(column.get_row(row_index)).ljust(padded_width), end='', file=file)
            if col_index == len(self.columns) - 1:
                print("", file=file)

    def __str__(self):
        output = StringIO()
        self.print(file=output)
        return output.getvalue()

    def _validate_structure(self):
        """Verifies the table has columns, and each column has the same number of rows."""
        if not self.columns:
            raise IllegalArgumentException("Table has no columns.")

        if self.columns[0].is_empty:
            raise IllegalArgumentException(
                f"Table's 1st column ({self.columns[0].name}) has no data."
            )

        for col_index, column in enumerate(self.columns[1:], start=1):
            if column.is_empty:
                raise IllegalStateException(
                    f"Table column # {col_index + 1} ({column.name}) does not have any data."
                )

            if self.row_count != column.row_count:
                raise IllegalStateException(
                    f"Table column # {col_index + 1} ({column.name}) does not have same number of rows as 1st column."
                )
