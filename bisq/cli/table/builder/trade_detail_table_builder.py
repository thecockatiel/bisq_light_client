from bisq.cli.table.builder.abstract_trade_list_builder import AbstractTradeListBuilder
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.table import Table
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2
import pb_pb2


class TradeDetailTableBuilder(AbstractTradeListBuilder):

    def __init__(self, protos: "list[grpc_pb2.TradeInfo]"):
        super().__init__(TableType.TRADE_DETAIL_TBL, protos)

    def _is_pending_bsq_swap(self, trade: grpc_pb2.TradeInfo) -> bool:
        return trade.state == pb_pb2.BsqSwapTrade.State.PREPARATION

    def _is_completed_bsq_swap(self, trade: grpc_pb2.TradeInfo) -> bool:
        return trade.state == pb_pb2.BsqSwapTrade.State.COMPLETED

    def build(self) -> Table:
        """Build a single row trade detail table."""
        # A trade detail table only has one row.
        trade = self.protos[0]
        self._populate_columns(trade)
        columns = self._define_column_list(trade)
        return Table(columns)

    def _populate_columns(self, trade: grpc_pb2.TradeInfo):
        if self.is_bsq_swap_trade(trade):
            is_pending = self._is_pending_bsq_swap(trade)
            is_completed = self._is_completed_bsq_swap(trade)
            if is_pending == is_completed:
                raise IllegalStateException(
                    f"programmer error: trade must be either pending or completed, is pending={is_pending} and completed={is_completed}"
                )
            self._populate_bsq_swap_trade_columns(trade)
        else:
            self._populate_bisq_v1_trade_columns(trade)

    def _populate_bisq_v1_trade_columns(self, trade: grpc_pb2.TradeInfo):
        self.col_trade_id.add_row(trade.short_id)
        self.col_role.add_row(trade.role)
        self.col_price.add_row(trade.trade_price)
        self.col_amount.add_row(self.to_trade_amount(trade))
        self.col_miner_tx_fee.add_row(self.to_my_miner_tx_fee(trade))
        self.col_bisq_trade_fee.add_row(self.to_my_maker_or_taker_fee(trade))
        self.col_is_deposit_published.add_row(trade.is_deposit_published)
        self.col_is_deposit_confirmed.add_row(trade.is_deposit_confirmed)
        self.col_trade_cost.add_row(self.to_trade_volume_as_string(trade))
        self.col_is_payment_started_message_sent.add_row(
            trade.is_payment_started_message_sent
        )
        self.col_is_payment_received_message_sent.add_row(
            trade.is_payment_received_message_sent
        )
        self.col_is_payout_published.add_row(trade.is_payout_published)
        self.col_is_completed.add_row(trade.is_completed)
        if self.col_altcoin_receive_address_column is not None:
            self.col_altcoin_receive_address_column.add_row(
                self.to_altcoin_receive_address(trade)
            )

    def _populate_bsq_swap_trade_columns(self, trade: grpc_pb2.TradeInfo):
        self.col_trade_id.add_row(trade.short_id)
        self.col_role.add_row(trade.role)
        self.col_price.add_row(trade.trade_price)
        self.col_amount.add_row(self.to_trade_amount(trade))
        self.col_miner_tx_fee.add_row(self.to_my_miner_tx_fee(trade))
        self.col_bisq_trade_fee.add_row(self.to_my_maker_or_taker_fee(trade))

        self.col_trade_cost.add_row(self.to_trade_volume_as_string(trade))

        is_completed = self._is_completed_bsq_swap(trade)
        self.status.add_row("COMPLETED" if is_completed else "PENDING")
        if is_completed:
            self.col_tx_id.add_row(trade.bsq_swap_trade_info.tx_id)
            self.col_num_confirmations.add_row(
                trade.bsq_swap_trade_info.num_confirmations
            )

    def _define_column_list(self, trade: grpc_pb2.TradeInfo) -> list:
        if self.is_bsq_swap_trade(trade):
            return self._get_bsq_swap_trade_column_list(
                self._is_completed_bsq_swap(trade)
            )
        else:
            return self._get_bisq_v1_trade_column_list()

    def _get_bisq_v1_trade_column_list(self) -> list:
        columns = [
            self.col_trade_id,
            self.col_role,
            self.col_price.justify(),
            self.col_amount.as_string_column(),
            self.col_miner_tx_fee.as_string_column(),
            self.col_bisq_trade_fee.as_string_column(),
            self.col_is_deposit_published.as_string_column(),
            self.col_is_deposit_confirmed.as_string_column(),
            self.col_trade_cost.justify(),
            self.col_is_payment_started_message_sent.as_string_column(),
            self.col_is_payment_received_message_sent.as_string_column(),
            self.col_is_payout_published.as_string_column(),
            self.col_is_completed.as_string_column(),
        ]

        if self.col_altcoin_receive_address_column is not None:
            columns.append(self.col_altcoin_receive_address_column)

        return columns

    def _get_bsq_swap_trade_column_list(self, is_completed: bool) -> list:
        columns = [
            self.col_trade_id,
            self.col_role,
            self.col_price.justify(),
            self.col_amount.as_string_column(),
            self.col_miner_tx_fee.as_string_column(),
            self.col_bisq_trade_fee.as_string_column(),
            self.col_trade_cost.justify(),
            self.status,
        ]

        if is_completed:
            columns.append(self.col_tx_id)

        if self.col_num_confirmations:
            columns.append(self.col_num_confirmations.as_string_column())

        return columns
