from bisq.cli.table.builder.abstract_trade_list_builder import AbstractTradeListBuilder
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.table import Table
import grpc_pb2


class ClosedTradeTableBuilder(AbstractTradeListBuilder):
    def __init__(self, protos: "list[grpc_pb2.TradeInfo]"):
        super().__init__(TableType.CLOSED_TRADES_TBL, protos)

    def build(self) -> Table:
        self._populate_columns()
        return Table(
            self.col_trade_id,
            self.col_create_date.as_string_column(),
            self.col_market,
            self.col_price.justify(),
            self.col_price_deviation.justify(),
            self.col_amount.as_string_column(),
            self.col_mixed_amount.justify(),
            self.col_currency,
            self.col_miner_tx_fee.as_string_column(),
            self.col_mixed_trade_fee.as_string_column(),
            self.col_buyer_deposit.as_string_column(),
            self.col_seller_deposit.as_string_column(),
            self.col_offer_type,
            self.col_closing_status,
        )

    def _populate_columns(self):
        for trade in self.protos:
            self.col_trade_id.add_row(trade.trade_id)
            self.col_create_date.add_row(trade.date)
            self.col_market.add_row(self.to_market(trade))
            self.col_price.add_row(trade.trade_price)
            self.col_price_deviation.add_row(self.to_price_deviation(trade))
            self.col_amount.add_row(trade.trade_amount_as_long)
            self.col_mixed_amount.add_row(trade.trade_volume)
            self.col_currency.add_row(self.to_payment_currency_code(trade))
            self.col_miner_tx_fee.add_row(self.to_my_miner_tx_fee(trade))

            if trade.offer.is_bsq_swap_offer:
                # For BSQ Swaps, BTC buyer pays the BSQ trade fee for both sides (BTC seller pays no fee).
                optional_trade_fee_bsq = (
                    0 if self.is_btc_seller(trade) else self.to_trade_fee_bsq(trade)
                )
                self.col_mixed_trade_fee.add_row(optional_trade_fee_bsq, True)
            elif self.is_trade_fee_btc(trade):
                self.col_mixed_trade_fee.add_row(self.to_trade_fee_btc(trade), False)
            else:
                # V1 trade fee paid in BSQ.
                self.col_mixed_trade_fee.add_row(self.to_trade_fee_bsq(trade), True)

            self.col_buyer_deposit.add_row(trade.offer.buyer_security_deposit)
            self.col_seller_deposit.add_row(trade.offer.seller_security_deposit)
            self.col_offer_type.add_row(self.to_offer_type(trade))
            self.col_closing_status.add_row(trade.closing_status)
