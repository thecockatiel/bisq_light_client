from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.number_column import NumberColumn


class MixedTradeFeeColumn(NumberColumn):
    """For displaying a mix of BSQ and BTC trade fees with appropriate precision."""

    def __init__(self, name: str):
        super().__init__(name, ColumnJustification.RIGHT)

    def add_row(self, value: int, is_bsq: bool):
        self.rows.append(value)

        s = (
            CurrencyFormat.format_bsq(value) + " BSQ"
            if is_bsq
            else CurrencyFormat.format_satoshis(value) + " BTC"
        )
        self.string_column.add_row(s)

        if self.is_new_max_width(s):
            self.max_width = len(s)

    def get_row_as_formatted_string(self, row_index: int) -> str:
        return str(self.get_row(row_index))

    def as_string_column(self):
        return self.string_column.justify()
