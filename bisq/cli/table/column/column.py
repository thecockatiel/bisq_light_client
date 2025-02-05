

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar
from bisq.cli.table.column.column_justification import ColumnJustification

if TYPE_CHECKING:
    from bisq.cli.table.column.string_column import StringColumn

_T = TypeVar('_T')

class Column(Generic[_T], ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the column's name."""
        pass
    
    @name.setter
    @abstractmethod
    def name(self, name: str):
        """Sets the column name."""
        pass

    @abstractmethod
    def add_row(self, value: _T):
        """Add a value to column's data (row)"""
        pass

    @property
    @abstractmethod
    def rows(self) -> list[_T]:
        """Returns the column data."""
        pass

    @property
    @abstractmethod
    def width(self) -> int:
        """
        Returns the maximum width of the column name, or longest,
        formatted string value -- whichever is greater.
        """
        pass

    @property
    @abstractmethod
    def row_count(self) -> int:
        """Returns the number of rows in the column."""
        pass

    @property
    @abstractmethod
    def is_empty(self, empty: bool):
        """Returns true if the column has no data."""
        pass

    @abstractmethod
    def get_row(self, row_index: int) -> _T:
        """Returns the column value (data) at given row index."""
        pass

    @abstractmethod
    def update_row(self, row_index: int, new_value: _T):
        """Update an existing value at the given row index to a new value."""
        pass

    @abstractmethod
    def get_row_as_formatted_string(self, row_index: int) -> str:
        """Returns the row value as a formatted String."""
        pass

    @abstractmethod
    def as_string_column(self) -> 'StringColumn':
        """
        Return the column with all of its data as a StringColumn with all of its
        formatted string data.
        """
        pass

    @abstractmethod
    def justify(self) -> 'Column[_T]':
        """
        Convenience for justifying populated StringColumns before being displayed.
        Is only useful for StringColumn instances.
        """
        pass

    @property
    @abstractmethod
    def justification(self) -> ColumnJustification:
        """Returns JUSTIFICATION value (RIGHT|LEFT|NONE) for the column."""
        pass
