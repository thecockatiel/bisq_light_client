from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.number_column import NumberColumn


class SatoshiColumn(NumberColumn):

    def __init__(self, name: str, justification: ColumnJustification = None, is_bsq_satoshis = False):
        if justification is None:
            justification = ColumnJustification.RIGHT
        super().__init__(name, justification)
        self._rows: list[int] = []
        self.max_width: int = len(name)
        self.is_bsq_satoshis = is_bsq_satoshis

    def add_row(self, value: int):
        self.rows.append(value)

        # We do not know how much padding each StringColumn value needs until it has all the values.
        s = CurrencyFormat.format_bsq(value) if self.is_bsq_satoshis else CurrencyFormat.format_satoshis(value)
        self.string_column.add_row(s)

        if self.is_new_max_width(s):
            self.max_width = len(s)

    def get_row_as_formatted_string(self, row_index: int) -> str:
        value = self.rows[row_index]
        return CurrencyFormat.format_bsq(value) if self.is_bsq_satoshis else CurrencyFormat.format_satoshis(value)

    def as_string_column(self):
        return self.string_column.justify()