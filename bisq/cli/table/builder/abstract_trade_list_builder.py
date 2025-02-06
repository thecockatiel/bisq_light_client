from decimal import Decimal
from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.builder.trade_table_column_supplier import TradeTableColumnSupplier
from bisq.cli.table.column.boolean_column import BooleanColumn
from bisq.cli.table.column.number_column import NumberColumn
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.column.string_column import StringColumn
from bisq.cli.table.table import Table
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
import grpc_pb2


class AbstractTradeListBuilder(AbstractTableBuilder["grpc_pb2.TradeInfo"]):
    def __init__(self, table_type: TableType, protos: list["grpc_pb2.TradeInfo"]):
        super().__init__(table_type, protos)
        self._validate()

        self.col_supplier = TradeTableColumnSupplier(table_type, self.protos)

        self.col_trade_id = self.col_supplier.trade_id_column()
        self.col_create_date = self.col_supplier.create_date_column()
        self.col_market = self.col_supplier.market_column()
        self.col_price = self.col_supplier.price_column()
        self.col_price_deviation = self.col_supplier.price_deviation_column()
        self.col_currency = self.col_supplier.currency_column()
        self.col_amount = self.col_supplier.amount_column()
        self.col_mixed_amount = self.col_supplier.mixed_amount_column()
        self.col_miner_tx_fee = self.col_supplier.miner_tx_fee_column()
        self.col_mixed_trade_fee = self.col_supplier.mixed_trade_fee_column()
        self.col_buyer_deposit = self.col_supplier.to_security_deposit_column(
            TableBuilderConstants.COL_HEADER_BUYER_DEPOSIT
        )
        self.col_seller_deposit = self.col_supplier.to_security_deposit_column(
            TableBuilderConstants.COL_HEADER_SELLER_DEPOSIT
        )
        self.col_payment_method = self.col_supplier.payment_method_column()
        self.col_role = self.col_supplier.role_column()
        self.col_offer_type = self.col_supplier.offer_type_column()
        self.col_closing_status = self.col_supplier.status_description_column()

        # Trade detail specific columns, some in common with BSQ swap trades detail.
        self.col_is_deposit_published = self.col_supplier.deposit_published_column()
        self.col_is_deposit_confirmed = self.col_supplier.deposit_confirmed_column()
        self.col_is_payout_published = self.col_supplier.payout_published_column()
        self.col_is_completed = self.col_supplier.funds_withdrawn_column()
        self.col_bisq_trade_fee = self.col_supplier.bisq_trade_detail_fee_column()
        self.col_trade_cost = self.col_supplier.trade_cost_column()
        self.col_is_payment_started_message_sent = (
            self.col_supplier.payment_started_message_sent_column()
        )
        self.col_is_payment_received_message_sent = (
            self.col_supplier.payment_received_message_sent_column()
        )
        self.col_altcoin_receive_address_column = (
            self.col_supplier.altcoin_receive_address_column()
        )

        # BSQ swap trade detail specific columns
        self.status = self.col_supplier.bsq_swap_status_column()
        self.col_tx_id = self.col_supplier.bsq_swap_tx_id_column()
        self.col_num_confirmations = self.col_supplier.num_confirmations_column()

    def _validate(self):
        if self._is_trade_detail_tbl_builder:
            if len(self.protos) != 1:
                raise IllegalArgumentException("trade detail tbl can have only one row")
        elif not self.protos:
            raise IllegalArgumentException("trade tbl has no rows")
        elif any(not isinstance(p, grpc_pb2.TradeInfo) for p in self.protos):
            raise IllegalArgumentException("trade tbl has non-trade rows")

    # Helper Functions

    @property
    def _is_trade_detail_tbl_builder(self):
        return self.table_type == TableType.TRADE_DETAIL_TBL

    def is_fiat_trade(self, trade: grpc_pb2.TradeInfo) -> bool:
        return super().is_fiat_offer(trade.offer)

    def is_bsq_trade(self, trade: grpc_pb2.TradeInfo) -> bool:
        return (
            not super().is_fiat_offer(trade.offer)
            and trade.offer.base_currency_code == "BSQ"
        )

    def is_bsq_swap_trade(self, trade: grpc_pb2.TradeInfo) -> bool:
        return trade.offer.is_bsq_swap_offer

    def is_my_offer(self, trade: grpc_pb2.TradeInfo) -> bool:
        return trade.offer.is_my_offer

    def is_taker(self, trade: grpc_pb2.TradeInfo) -> bool:
        return "taker" in trade.role.lower()

    def is_sell_offer(self, trade: grpc_pb2.TradeInfo) -> bool:
        return trade.offer.direction == "SELL"

    def is_btc_seller(self, trade: grpc_pb2.TradeInfo) -> bool:
        return (self.is_my_offer(trade) and self.is_sell_offer(trade)) or (
            not self.is_my_offer(trade) and not self.is_sell_offer(trade)
        )

    def is_trade_fee_btc(self, trade: grpc_pb2.TradeInfo) -> bool:
        return (
            trade.offer.is_currency_for_maker_fee_btc
            if self.is_my_offer(trade)
            else trade.is_currency_for_taker_fee_btc
        )

    # Column Value Functions

    # Altcoin volumes from server are string representations of decimals.
    # Converting them to longs ("sats") requires shifting the decimal points
    # to left:  2 for BSQ, 8 for other altcoins.
    # (probably not needed in python implementation, but we do it anyway for consistency)
    def to_altcoin_trade_volume_as_long(self, trade: grpc_pb2.TradeInfo) -> int:
        d = Decimal(trade.trade_volume)
        if self.is_bsq_trade(trade):
            return int(d.scaleb(2))
        return int(d.scaleb(8))

    def to_trade_volume_as_string(self, trade: grpc_pb2.TradeInfo) -> str:
        if self.is_fiat_trade(trade):
            return trade.trade_volume
        return CurrencyFormat.format_satoshis(trade.trade_amount_as_long)

    def to_trade_volume_as_long(self, trade: grpc_pb2.TradeInfo) -> int:
        if self.is_fiat_trade(trade):
            return int(trade.trade_volume)
        return self.to_altcoin_trade_volume_as_long(trade)

    def to_trade_amount(self, trade: grpc_pb2.TradeInfo) -> int:
        if self.is_fiat_trade(trade):
            return trade.trade_amount_as_long
        return self.to_trade_volume_as_long(trade)

    def to_market(self, trade: grpc_pb2.TradeInfo) -> str:
        return f"{trade.offer.base_currency_code}/{trade.offer.counter_currency_code}"

    def to_payment_currency_code(self, trade: grpc_pb2.TradeInfo) -> str:
        return (
            trade.offer.counter_currency_code
            if self.is_fiat_trade(trade)
            else trade.offer.base_currency_code
        )

    def to_price_deviation(self, trade: grpc_pb2.TradeInfo) -> str:
        if trade.offer.use_market_based_price:
            return f"{trade.offer.market_price_margin_pct:.2f}%"
        return "N/A"

    def to_my_miner_tx_fee(self, trade: grpc_pb2.TradeInfo) -> int:
        if self.is_bsq_swap_trade(trade):
            # The BTC seller pays the miner fee for both sides.
            return trade.tx_fee_as_long if self.is_btc_seller(trade) else 0
        return trade.tx_fee_as_long if self.is_taker(trade) else trade.offer.tx_fee

    def to_trade_fee_bsq(self, trade: grpc_pb2.TradeInfo) -> int:
        is_my_offer = trade.offer.is_my_offer
        if is_my_offer:
            return (
                0  # Maker paid BTC fee, return 0
                if trade.offer.is_currency_for_maker_fee_btc
                else trade.offer.maker_fee
            )
        else:
            return (
                0  # Taker paid BTC fee, return 0.
                if trade.is_currency_for_taker_fee_btc
                else trade.taker_fee_as_long
            )

    def to_trade_fee_btc(self, trade: grpc_pb2.TradeInfo) -> int:
        is_my_offer = trade.offer.is_my_offer
        if is_my_offer:
            return (
                trade.offer.maker_fee
                if trade.offer.is_currency_for_maker_fee_btc
                else 0  # Maker paid BSQ fee, return 0.
            )
        else:
            return (
                trade.taker_fee_as_long
                if trade.is_currency_for_taker_fee_btc
                else 0  # Taker paid BSQ fee, return 0.
            )

    def to_my_maker_or_taker_fee(self, trade: grpc_pb2.TradeInfo) -> int:
        if self.is_bsq_swap_trade(trade):
            return (
                trade.bsq_swap_trade_info.bsq_taker_trade_fee
                if self.is_taker(trade)
                else trade.bsq_swap_trade_info.bsq_maker_trade_fee
            )
        else:
            return (
                trade.taker_fee_as_long
                if self.is_taker(trade)
                else trade.offer.maker_fee
            )

    def to_offer_type(self, trade: grpc_pb2.TradeInfo) -> str:
        if self.is_fiat_trade(trade):
            return f"{trade.offer.direction} {trade.offer.base_currency_code}"
        else:
            if trade.offer.direction == "BUY":
                return f"SELL {trade.offer.base_currency_code}"
            else:
                return f"BUY {trade.offer.base_currency_code}"

    def show_altcoin_buyer_address(self, trade: grpc_pb2.TradeInfo) -> bool:
        if self.is_fiat_trade(trade):
            return False
        else:
            contract = trade.contract
            is_buyer_maker_and_seller_taker = contract.is_buyer_maker_and_seller_taker
            if self.is_taker(trade):
                return not is_buyer_maker_and_seller_taker
            else:
                return is_buyer_maker_and_seller_taker

    def to_altcoin_receive_address(self, trade: grpc_pb2.TradeInfo) -> str:
        if self.show_altcoin_buyer_address(trade):
            contract = trade.contract
            is_buyer_maker_and_seller_taker = contract.is_buyer_maker_and_seller_taker
            return (
                contract.taker_payment_account_payload.address
                if is_buyer_maker_and_seller_taker  # (is BTC buyer / maker)
                else contract.maker_payment_account_payload.address
            )
        else:
            return ""
