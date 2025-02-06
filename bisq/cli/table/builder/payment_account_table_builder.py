from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.string_column import StringColumn
from bisq.cli.table.table import Table
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import pb_pb2


class PaymentAccountTableBuilder(AbstractTableBuilder["pb_pb2.PaymentAccount"]):
    def __init__(self, protos: list["pb_pb2.PaymentAccount"]):
        super().__init__(TableType.PAYMENT_ACCOUNT_TBL, protos)
        # check if protos are really instanes of PaymentAccount
        if not all(isinstance(proto, pb_pb2.PaymentAccount) for proto in protos):
            raise IllegalStateException(
                "Protos must all be instances of PaymentAccount"
            )
        # Default columns not dynamically generated with payment account info.
        self.col_name = StringColumn(TableBuilderConstants.COL_HEADER_NAME)
        self.col_currency = StringColumn(TableBuilderConstants.COL_HEADER_CURRENCY)
        self.col_payment_method = StringColumn(
            TableBuilderConstants.COL_HEADER_PAYMENT_METHOD
        )
        self.col_id = StringColumn(TableBuilderConstants.COL_HEADER_UUID)

    def build(self) -> Table:

        # Populate columns with payment account info.
        for account in self.protos:
            self.col_name.add_row(account.account_name)
            self.col_currency.add_row(account.selected_trade_currency.code)
            self.col_payment_method.add_row(account.payment_method.id)
            self.col_id.add_row(account.id)

        # Define and return the table instance with populated columns.
        return Table(
            self.col_name, self.col_currency, self.col_payment_method, self.col_id
        )
