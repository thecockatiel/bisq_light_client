from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.table.column.satoshi_column import SatoshiColumn


class BtcColumn(SatoshiColumn):

    def __init__(self, name: str):
        super().__init__(name)

    def add_row(self, value: int):
        self.rows.append(value)

        # We do not know how much padding each StringColumn value needs until it has all the values.
        s = CurrencyFormat.format_btc(value)
        self.string_column.add_row(s)

        if self.is_new_max_width(s):
            self.max_width = len(s)

    def get_row_as_formatted_string(self, row_index: int) -> str:
        return CurrencyFormat.format_btc(self.get_row(row_index))

    def as_string_column(self):
        # We cached the formatted satoshi strings, but we did
        # not know how much zero padding each string needed until now.
        max_column_value_width = max(len(row) for row in self.string_column.rows)
        for row_index, btc_string in enumerate(self.string_column.rows):
            if len(btc_string) < max_column_value_width:
                padded_btc_string = btc_string.ljust(max_column_value_width, "0")
                self.string_column.update_row(row_index, padded_btc_string)
        return self.string_column.justify()
