from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.altcoin_volume_column import AltcoinVolumeColumn
from bisq.cli.table.column.boolean_column import BooleanColumn
from bisq.cli.table.column.btc_column import BtcColumn
from bisq.cli.table.column.column import Column
from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.iso8601_date_time_column import Iso8601DateTimeColumn
from bisq.cli.table.column.mixed_trade_fee_column import MixedTradeFeeColumn
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.column.string_column import StringColumn
from grpc_pb2 import OfferInfo, TradeInfo
from typing import List


class TradeTableColumnSupplier:
    """
    Convenience for supplying column definitions to
    open/closed/failed/detail trade table builders.
    """

    def __init__(self, table_type: TableType, trades: List[TradeInfo]):
        self._table_type = table_type
        self._trades = trades

    @property
    def table_type(self):
        return self._table_type

    @property
    def trades(self):
        return self._trades

    @property
    def _is_trade_detail_tbl_builder(self):
        return self._table_type == TableType.TRADE_DETAIL_TBL

    @property
    def _is_open_trade_tbl_builder(self):
        return self._table_type == TableType.OPEN_TRADES_TBL

    @property
    def _is_closed_trade_tbl_builder(self):
        return self._table_type == TableType.CLOSED_TRADES_TBL

    @property
    def _is_failed_trade_tbl_builder(self):
        return self._table_type == TableType.FAILED_TRADES_TBL

    @property
    def _first_row(self):
        return self._trades[0]

    def _is_fiat_offer(self, offer: OfferInfo):
        return offer.base_currency_code == "BTC"

    def _is_fiat_trade(self, trade: TradeInfo):
        return self._is_fiat_offer(trade.offer)

    def _is_bsq_swap_trade(self, trade: TradeInfo):
        return trade.offer.is_bsq_swap_offer

    def _is_taker(self, trade: TradeInfo):
        return "taker" in trade.role.lower()

    @property
    def _is_swap_trade_detail(self):
        return self._is_trade_detail_tbl_builder and self._is_bsq_swap_trade(
            self._first_row
        )

    def trade_id_column(self):
        if self._is_trade_detail_tbl_builder:
            return StringColumn(TableBuilderConstants.COL_HEADER_TRADE_SHORT_ID)
        else:
            return StringColumn(TableBuilderConstants.COL_HEADER_TRADE_ID)

    def create_date_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return Iso8601DateTimeColumn(TableBuilderConstants.COL_HEADER_DATE_TIME)

    def market_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return StringColumn(TableBuilderConstants.COL_HEADER_MARKET)

    def _to_detailed_price_column(self, t: TradeInfo):
        if self._is_fiat_trade(t):
            col_header = TableBuilderConstants.COL_HEADER_DETAILED_PRICE.format(
                t.offer.counter_currency_code
            )
        else:
            col_header = (
                TableBuilderConstants.COL_HEADER_DETAILED_PRICE_OF_ALTCOIN.format(
                    t.offer.base_currency_code
                )
            )

        return StringColumn(col_header, ColumnJustification.RIGHT)

    def price_column(self):
        if self._is_trade_detail_tbl_builder:
            return self._to_detailed_price_column(self._first_row)
        else:
            return StringColumn(
                TableBuilderConstants.COL_HEADER_PRICE, ColumnJustification.RIGHT
            )

    def price_deviation_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return StringColumn(
                TableBuilderConstants.COL_HEADER_DEVIATION, ColumnJustification.RIGHT
            )

    def currency_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return StringColumn(TableBuilderConstants.COL_HEADER_CURRENCY)

    def _to_detailed_amount_column(self, t: TradeInfo):
        header_currency_code = t.offer.base_currency_code
        col_header = TableBuilderConstants.COL_HEADER_DETAILED_AMOUNT.format(
            header_currency_code
        )
        display_mode = (
            AltcoinVolumeColumn.DISPLAY_MODE.BSQ_VOLUME
            if header_currency_code == "BSQ"
            else AltcoinVolumeColumn.DISPLAY_MODE.ALTCOIN_VOLUME
        )
        if self._is_fiat_trade(t):
            return SatoshiColumn(col_header)
        else:
            return AltcoinVolumeColumn(col_header, display_mode)

    # Can be fiat, btc or altcoin amount represented as longs.  Placing the decimal
    # in the displayed string representation is done in the Column implementation.
    def amount_column(self):
        if self._is_trade_detail_tbl_builder:
            return self._to_detailed_amount_column(self._first_row)
        else:
            return BtcColumn(TableBuilderConstants.COL_HEADER_AMOUNT_IN_BTC)

    def mixed_amount_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return StringColumn(
                TableBuilderConstants.COL_HEADER_AMOUNT, ColumnJustification.RIGHT
            )

    def miner_tx_fee_column(self):
        if self._is_trade_detail_tbl_builder or self._is_closed_trade_tbl_builder:
            return SatoshiColumn(TableBuilderConstants.COL_HEADER_TX_FEE)
        else:
            return None

    def mixed_trade_fee_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return MixedTradeFeeColumn(TableBuilderConstants.COL_HEADER_TRADE_FEE)

    def payment_method_column(self):
        if self._is_trade_detail_tbl_builder or self._is_closed_trade_tbl_builder:
            return None
        else:
            return StringColumn(
                TableBuilderConstants.COL_HEADER_PAYMENT_METHOD,
                ColumnJustification.LEFT,
            )

    def role_column(self):
        if self._is_swap_trade_detail:
            return StringColumn(TableBuilderConstants.COL_HEADER_BSQ_SWAP_TRADE_ROLE)
        elif (
            self._is_trade_detail_tbl_builder
            or self._is_open_trade_tbl_builder
            or self._is_failed_trade_tbl_builder
        ):
            return StringColumn(TableBuilderConstants.COL_HEADER_TRADE_ROLE)
        else:
            return None

    def to_security_deposit_column(self, name: str):
        if self._is_closed_trade_tbl_builder:
            return SatoshiColumn(name)
        else:
            return None

    def offer_type_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return StringColumn(TableBuilderConstants.COL_HEADER_OFFER_TYPE)

    def status_description_column(self):
        if self._is_trade_detail_tbl_builder:
            return None
        else:
            return StringColumn(TableBuilderConstants.COL_HEADER_STATUS)

    def _to_boolean_column(self, name: str):
        return BooleanColumn(name)

    def deposit_published_column(self):
        if self._is_swap_trade_detail:
            return None
        elif self._is_trade_detail_tbl_builder:
            return self._to_boolean_column(
                TableBuilderConstants.COL_HEADER_TRADE_DEPOSIT_PUBLISHED
            )
        else:
            return None

    def deposit_confirmed_column(self):
        if self._is_swap_trade_detail:
            return None
        elif self._is_trade_detail_tbl_builder:
            return self._to_boolean_column(
                TableBuilderConstants.COL_HEADER_TRADE_DEPOSIT_CONFIRMED
            )
        else:
            return None

    def payout_published_column(self):
        if self._is_swap_trade_detail:
            return None
        elif self._is_trade_detail_tbl_builder:
            return self._to_boolean_column(
                TableBuilderConstants.COL_HEADER_TRADE_PAYOUT_PUBLISHED
            )
        else:
            return None

    def funds_withdrawn_column(self):
        if self._is_swap_trade_detail:
            return None
        elif self._is_trade_detail_tbl_builder:
            return self._to_boolean_column(
                TableBuilderConstants.COL_HEADER_TRADE_WITHDRAWN
            )
        else:
            return None

    def bisq_trade_detail_fee_column(self):
        if self._is_trade_detail_tbl_builder:
            t = self._first_row
            if self._is_taker(t):
                if t.is_currency_for_taker_fee_btc:
                    header_currency_code = "BTC"
                else:
                    header_currency_code = "BSQ"
            else:
                if t.offer.is_currency_for_maker_fee_btc:
                    header_currency_code = "BTC"
                else:
                    header_currency_code = "BSQ"
            col_header = (
                TableBuilderConstants.COL_HEADER_TRADE_TAKER_FEE.format(
                    header_currency_code
                )
                if self._is_taker(t)
                else TableBuilderConstants.COL_HEADER_TRADE_MAKER_FEE.format(
                    header_currency_code
                )
            )
            is_bsq_satoshis = header_currency_code == "BSQ"
            return SatoshiColumn(col_header, is_bsq_satoshis=is_bsq_satoshis)
        else:
            return None

    def to_payment_currency_code(self, trade: TradeInfo) -> str:
        if self._is_fiat_trade(trade):
            return trade.offer.counter_currency_code
        else:
            return trade.offer.base_currency_code

    def payment_started_message_sent_column(self):
        if self._is_trade_detail_tbl_builder:
            header_currency_code = self.to_payment_currency_code(self._first_row)
            col_header = TableBuilderConstants.COL_HEADER_TRADE_PAYMENT_SENT.format(
                header_currency_code
            )
            return BooleanColumn(col_header)
        else:
            return None

    def payment_received_message_sent_column(self):
        if self._is_trade_detail_tbl_builder:
            header_currency_code = self.to_payment_currency_code(self._first_row)
            col_header = TableBuilderConstants.COL_HEADER_TRADE_PAYMENT_RECEIVED.format(
                header_currency_code
            )
            return BooleanColumn(col_header)
        else:
            return None

    def trade_cost_column(self):
        if self._is_trade_detail_tbl_builder:
            t = self._first_row
            header_currency_code = t.offer.counter_currency_code
            col_header = TableBuilderConstants.COL_HEADER_TRADE_BUYER_COST.format(
                header_currency_code
            )
            return StringColumn(col_header, ColumnJustification.RIGHT)
        else:
            return None

    def bsq_swap_tx_id_column(self):
        if self._is_swap_trade_detail:
            return StringColumn(TableBuilderConstants.COL_HEADER_TX_ID)
        else:
            return None

    def bsq_swap_status_column(self):
        if self._is_swap_trade_detail:
            return StringColumn(TableBuilderConstants.COL_HEADER_STATUS)
        else:
            return None

    def num_confirmations_column(self):
        if self._is_swap_trade_detail:
            return Column(TableBuilderConstants.COL_HEADER_CONFIRMATIONS)
        else:
            return None

    def show_altcoin_buyer_address(self, trade: TradeInfo) -> bool:
        if self._is_fiat_trade(trade):
            return False
        else:
            contract = trade.contract
            is_buyer_maker_and_seller_taker = contract.is_buyer_maker_and_seller_taker
            if self._is_taker(trade):
                return not is_buyer_maker_and_seller_taker
            else:
                return is_buyer_maker_and_seller_taker

    def altcoin_receive_address_column(self):
        if self._is_trade_detail_tbl_builder:
            t = self._first_row
            if self.show_altcoin_buyer_address(t):
                header_currency_code = self.to_payment_currency_code(t)
                col_header = (
                    TableBuilderConstants.COL_HEADER_TRADE_ALTCOIN_BUYER_ADDRESS.format(
                        header_currency_code
                    )
                )
                return StringColumn(col_header)
            else:
                return None
        else:
            return None
