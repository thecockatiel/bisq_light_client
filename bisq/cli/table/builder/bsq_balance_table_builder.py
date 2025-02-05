from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.table import Table
import grpc_pb2


class BsqBalanceTableBuilder(AbstractTableBuilder):
    def __init__(self, protos: list):
        super().__init__(TableType.BSQ_BALANCE_TBL, protos)
        # Default columns not dynamically generated with bsq balance info.
        self.col_available_confirmed_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_AVAILABLE_CONFIRMED_BALANCE,
            is_bsq_satoshis=True,
        )
        self.col_unverified_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_UNVERIFIED_BALANCE, is_bsq_satoshis=True
        )
        self.col_unconfirmed_change_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_UNCONFIRMED_CHANGE_BALANCE,
            is_bsq_satoshis=True,
        )
        self.col_locked_for_voting_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_LOCKED_FOR_VOTING_BALANCE,
            is_bsq_satoshis=True,
        )
        self.col_lockup_bonds_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_LOCKUP_BONDS_BALANCE, is_bsq_satoshis=True
        )
        self.col_unlocking_bonds_balance = SatoshiColumn(
            TableBuilderConstants.COL_HEADER_UNLOCKING_BONDS_BALANCE,
            is_bsq_satoshis=True,
        )

    def build(self):
        balance: grpc_pb2.BsqBalanceInfo = self.protos[0]

        # Populate columns with bsq balance info.
        self.col_available_confirmed_balance.add_row(
            balance.available_confirmed_balance
        )
        self.col_unverified_balance.add_row(balance.unverified_balance)
        self.col_unconfirmed_change_balance.add_row(balance.unconfirmed_change_balance)
        self.col_locked_for_voting_balance.add_row(balance.locked_for_voting_balance)
        self.col_lockup_bonds_balance.add_row(balance.lockup_bonds_balance)
        self.col_unlocking_bonds_balance.add_row(balance.unlocking_bonds_balance)

        # Define and return the table instance with populated columns.
        return Table(
            self.col_available_confirmed_balance.as_string_column(),
            self.col_unverified_balance.as_string_column(),
            self.col_unconfirmed_change_balance.as_string_column(),
            self.col_locked_for_voting_balance.as_string_column(),
            self.col_lockup_bonds_balance.as_string_column(),
            self.col_unlocking_bonds_balance.as_string_column(),
        )
