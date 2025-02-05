from typing import TypeVar, Union
from bisq.cli.table.column.abstract_column import AbstractColumn
from bisq.cli.table.column.column import Column

_N = Union[int, float]
_T = TypeVar("_T", bound=_N)
_C = TypeVar("_C", bound="NumberColumn")

class NumberColumn(AbstractColumn[_C, _T], Column[_T]):
    pass
