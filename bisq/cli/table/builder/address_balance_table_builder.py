from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.boolean_column import BooleanColumn
from bisq.cli.table.column.number_column import NumberColumn
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.column.string_column import StringColumn
from bisq.cli.table.table import Table
import grpc_pb2


class AddressBalanceTableBuilder(AbstractTableBuilder["grpc_pb2.AddressBalanceInfo"]):
    def __init__(self, protos: list[grpc_pb2.AddressBalanceInfo]):
        super().__init__(TableType.ADDRESS_BALANCE_TBL, protos)
        self.col_address = StringColumn(
            TableBuilderConstants.COL_HEADER_ADDRESS.format("BTC")
        )
        self.col_available_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_AVAILABLE_BALANCE
        )
        self.col_confirmations = NumberColumn(
            TableBuilderConstants.COL_HEADER_CONFIRMATIONS
        )
        self.col_is_used = BooleanColumn(
            TableBuilderConstants.COL_HEADER_IS_USED_ADDRESS
        )

    def build(self):
        for a in self.protos:
            self.col_address.add_row(a.address)
            self.col_available_balance.add_row(a.balance)
            self.col_confirmations.add_row(a.num_confirmations)
            self.col_is_used.add_row(not a.is_address_unused)

        return Table(
            self.col_address,
            self.col_available_balance.as_string_column(),
            self.col_confirmations.as_string_column(),
            self.col_is_used.as_string_column(),
        )
