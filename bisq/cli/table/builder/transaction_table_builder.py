from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.boolean_column import BooleanColumn
from bisq.cli.table.column.number_column import NumberColumn
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.column.string_column import StringColumn
from bisq.cli.table.table import Table
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2


class TransactionTableBuilder(AbstractTableBuilder["grpc_pb2.TxInfo"]):
    def __init__(self, protos: list["grpc_pb2.TxInfo"]):
        super().__init__(TableType.TRANSACTION_TBL, protos)
        if not all(isinstance(proto, grpc_pb2.TxInfo) for proto in protos):
            raise IllegalStateException(
                "protos must all be instances of grpc_pb2.TxInfo"
            )
        #  Default columns not dynamically generated with tx info.
        self.col_tx_id = StringColumn(TableBuilderConstants.COL_HEADER_TX_ID)
        self.col_is_confirmed = BooleanColumn(
            TableBuilderConstants.COL_HEADER_TX_IS_CONFIRMED
        )
        self.col_input_sum = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_TX_INPUT_SUM
        )
        self.col_output_sum = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_TX_OUTPUT_SUM
        )
        self.col_tx_fee = SatoshiColumn(TableBuilderConstants.COL_HEADER_TX_FEE)
        self.col_tx_size = NumberColumn(TableBuilderConstants.COL_HEADER_TX_SIZE)
        self.col_memo = StringColumn(TableBuilderConstants.COL_HEADER_TX_MEMO)

    def build(self) -> Table:
        for proto in self.protos:
            self.col_tx_id.add_row(proto.tx_id)
            self.col_is_confirmed.add_row(not proto.is_pending)
            self.col_input_sum.add_row(proto.input_sum)
            self.col_output_sum.add_row(proto.output_sum)
            self.col_tx_fee.add_row(proto.fee)
            self.col_tx_size.add_row(proto.size)
            self.col_memo.add_row(proto.memo)

        columns = [
            self.col_tx_id,
            self.col_is_confirmed.as_string_column(),
            self.col_input_sum.as_string_column(),
            self.col_output_sum.as_string_column(),
            self.col_tx_fee.as_string_column(),
            self.col_tx_size.as_string_column(),
        ]

        if self.col_memo:
            columns.append(self.col_memo)

        return Table(*columns)
