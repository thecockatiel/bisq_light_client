from bisq.cli.table.builder.abstract_trade_list_builder import AbstractTradeListBuilder
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.table import Table
import grpc_pb2


class OpenTradeTableBuilder(AbstractTradeListBuilder):
    def __init__(self, protos: "list[grpc_pb2.TradeInfo]"):
        super().__init__(TableType.OPEN_TRADES_TBL, protos)

    def build(self) -> Table:
        self._populate_columns()
        return Table(
            self.col_trade_id,
            self.col_create_date.as_string_column(),
            self.col_market,
            self.col_price.justify(),
            self.col_amount.as_string_column(),
            self.col_mixed_amount.justify(),
            self.col_currency,
            self.col_payment_method,
            self.col_role,
        )

    def _populate_columns(self):
        for trade in self.protos:
            self.col_trade_id.add_row(trade.trade_id)
            self.col_create_date.add_row(trade.date)
            self.col_market.add_row(self.to_market(trade))
            self.col_price.add_row(trade.trade_price)
            self.col_amount.add_row(trade.trade_amount_as_long)
            self.col_mixed_amount.add_row(trade.trade_volume)
            self.col_currency.add_row(self.to_payment_currency_code(trade))
            self.col_payment_method.add_row(trade.offer.payment_method_short_name)
            self.col_role.add_row(trade.role)
