from decimal import Decimal
from enum import IntEnum, auto
from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.number_column import NumberColumn
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


class AltcoinVolumeColumn(NumberColumn[int]):
    """For displaying altcoin volume with appropriate precision."""

    class DISPLAY_MODE(IntEnum):
        ALTCOIN_VOLUME = auto()
        BSQ_VOLUME = auto()

    def __init__(
        self,
        name: str,
        display_mode: "DISPLAY_MODE",
        justification: ColumnJustification = None,
    ):
        if justification is None:
            justification = ColumnJustification.RIGHT
        super().__init__(name, justification)
        self.display_mode = display_mode

    def add_row(self, value: int):
        self.rows.append(value)

        s = self._to_formatted_string(value, self.display_mode)
        self.string_column.add_row(s)

        if self.is_new_max_width(s):
            self.max_width = len(s)

    def get_row_as_formatted_string(self, row_index: int) -> str:
        return self._to_formatted_string(self.get_row(row_index), self.display_mode)

    def as_string_column(self):
        # We cached the formatted altcoin value strings, but we did
        # not know how much padding each string needed until now.
        for row_index in range(self.string_column.row_count):
            unjustified = self.string_column.get_row(row_index)
            justified = self.string_column.to_justified_string(unjustified)
            self.string_column.update_row(row_index, justified)
        return self.string_column

    def _to_formatted_string(
        self, value: int, display_mode: "AltcoinVolumeColumn.DISPLAY_MODE"
    ) -> str:
        if display_mode == self.DISPLAY_MODE.ALTCOIN_VOLUME:
            return str(Decimal(value).scaleb(-8)) if value > 0 else ""
        elif display_mode == self.DISPLAY_MODE.BSQ_VOLUME:
            return str(Decimal(value).scaleb(-2)) if value > 0 else ""
        else:
            raise IllegalStateException(f"invalid display mode: {display_mode}")
