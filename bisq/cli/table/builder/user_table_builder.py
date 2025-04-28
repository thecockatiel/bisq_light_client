from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.boolean_column import BooleanColumn
from bisq.cli.table.column.number_column import NumberColumn
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.column.string_column import StringColumn
from bisq.cli.table.table import Table
import grpc_extra_pb2


class UserTableBuilder(AbstractTableBuilder["grpc_extra_pb2.BriefUserInfo"]):
    def __init__(self, protos: list[grpc_extra_pb2.BriefUserInfo]):
        super().__init__(TableType.USERS_TBL, protos)
        self.col_user_id = StringColumn(TableBuilderConstants.COL_HEADER_USER_ID)
        self.col_alias = StringColumn(TableBuilderConstants.COL_HEADER_ALIAS)

    def build(self):
        for u in self.protos:
            self.col_user_id.add_row(u.user_id)
            self.col_alias.add_row(u.alias)

        return Table(self.col_user_id, self.col_alias)
