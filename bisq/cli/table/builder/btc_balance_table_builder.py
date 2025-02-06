from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.table import Table
import grpc_pb2


class BtcBalanceTableBuilder(AbstractTableBuilder["grpc_pb2.BtcBalanceInfo"]):
    def __init__(self, protos: list[grpc_pb2.BtcBalanceInfo]):
        super().__init__(TableType.BTC_BALANCE_TBL, protos)
        # Default columns not dynamically generated with btc balance info.
        self.col_available_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_AVAILABLE_BALANCE,
        )
        self.col_reserved_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_RESERVED_BALANCE,
        )
        self.col_total_available_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_TOTAL_AVAILABLE_BALANCE,
        )
        self.col_locked_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_LOCKED_BALANCE,
        )

    def build(self):
        balance = self.protos[0]

        # Populate columns with btc balance info.
        self.col_available_balance.add_row(balance.available_balance)
        self.col_reserved_balance.add_row(balance.reserved_balance)
        self.col_total_available_balance.add_row(balance.total_available_balance)
        self.col_locked_balance.add_row(balance.locked_balance)

        # Define and return the table instance with populated columns.
        return Table(
            self.col_available_balance.as_string_column(),
            self.col_reserved_balance.as_string_column(),
            self.col_total_available_balance.as_string_column(),
            self.col_locked_balance.as_string_column(),
        )
