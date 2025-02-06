from typing import Optional
from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.table_builder_constants import TableBuilderConstants
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.column.column_justification import ColumnJustification
from bisq.cli.table.column.iso8601_date_time_column import Iso8601DateTimeColumn
from bisq.cli.table.column.satoshi_column import SatoshiColumn
from bisq.cli.table.column.string_column import StringColumn
from bisq.cli.table.column.zipped_string_columns import ZippedStringColumns
from bisq.cli.table.table import Table
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2


class OfferTableBuilder(AbstractTableBuilder):
    def __init__(self, protos: "list[grpc_pb2.OfferInfo]"):
        super().__init__(TableType.OFFER_TBL, protos)
        for proto in protos:
            if not isinstance(proto, grpc_pb2.OfferInfo):
                raise IllegalStateException(
                    "protos must all be instances of grpc_pb2.OfferInfo"
                )
        # Columns common to both fiat and cryptocurrency offers.
        self.col_offer_id = StringColumn(
            TableBuilderConstants.COL_HEADER_UUID, ColumnJustification.LEFT
        )
        self.col_direction = StringColumn(
            TableBuilderConstants.COL_HEADER_DIRECTION, ColumnJustification.LEFT
        )
        self.col_amount = SatoshiColumn("Temp Amount", ColumnJustification.NONE)
        self.col_min_amount = SatoshiColumn("Temp Min Amount", ColumnJustification.NONE)
        self.col_payment_method = StringColumn(
            TableBuilderConstants.COL_HEADER_PAYMENT_METHOD, ColumnJustification.LEFT
        )
        self.col_create_date = Iso8601DateTimeColumn(
            TableBuilderConstants.COL_HEADER_CREATION_DATE
        )

    def build(self) -> Table:
        if self._is_showing_fiat_offers():
            return self.build_fiat_offer_table(self.protos)
        else:
            return self.build_crypto_currency_offer_table(self.protos)

    def build_fiat_offer_table(self, offers: "list[grpc_pb2.OfferInfo]") -> Table:
        col_enabled = self._enabled_column()  # Not boolean: "YES", "NO", or "PENDING"
        col_fiat_price = StringColumn(
            TableBuilderConstants.COL_HEADER_DETAILED_PRICE.format(
                self._fiat_trade_currency()
            ),
            ColumnJustification.RIGHT,
        )
        col_volume = StringColumn(
            "Temp Volume ({})".format(self._fiat_trade_currency()),
            ColumnJustification.NONE,
        )
        col_min_volume = StringColumn(
            "Temp Min Volume ({})".format(self._fiat_trade_currency()),
            ColumnJustification.NONE,
        )
        col_trigger_price = self._fiat_trigger_price_column()

        # Populate columns with offer info.

        for offer in offers:
            if col_enabled:
                col_enabled.add_row(self._to_enabled(offer))

            self.col_direction.add_row(offer.direction)
            col_fiat_price.add_row(offer.price)
            self.col_min_amount.add_row(offer.min_amount)
            self.col_amount.add_row(offer.amount)
            col_volume.add_row(offer.volume)
            col_min_volume.add_row(offer.min_volume)

            if col_trigger_price:
                col_trigger_price.add_row(
                    self._to_blank_or_non_zero_value(offer.trigger_price)
                )

            self.col_payment_method.add_row(offer.payment_method_short_name)
            self.col_create_date.add_row(offer.date)
            self.col_offer_id.add_row(offer.id)

        amount_range = self._zipped_amount_range_columns()
        volume_range = ZippedStringColumns(
            TableBuilderConstants.COL_HEADER_VOLUME_RANGE.format(
                self._fiat_trade_currency()
            ),
            ColumnJustification.RIGHT,
            " - ",
            col_min_volume.as_string_column(),
            col_volume.as_string_column(),
        )

        # Define and return the table instance with populated columns.

        if self._is_showing_my_offers():
            return Table(
                col_enabled.as_string_column(),
                self.col_direction,
                col_fiat_price.justify(),
                amount_range.as_string_column(
                    ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                ),
                volume_range.as_string_column(
                    ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                ),
                col_trigger_price.justify(),  # is not none when showing my offers
                self.col_payment_method,
                self.col_create_date.as_string_column(),
                self.col_offer_id,
            )
        else:
            return Table(
                self.col_direction,
                col_fiat_price.justify(),
                amount_range.as_string_column(
                    ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                ),
                volume_range.as_string_column(
                    ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                ),
                self.col_payment_method,
                self.col_create_date.as_string_column(),
                self.col_offer_id,
            )

    def build_crypto_currency_offer_table(
        self, offers: "list[grpc_pb2.OfferInfo]"
    ) -> Table:
        col_enabled = self._enabled_column()  # Not boolean: "YES", "NO", or "PENDING"
        col_btc_price = StringColumn(
            TableBuilderConstants.COL_HEADER_DETAILED_PRICE_OF_ALTCOIN.format(
                self._altcoin_trade_currency()
            ),
            ColumnJustification.RIGHT,
        )
        col_volume = StringColumn(
            "Temp Volume ({})".format(self._altcoin_trade_currency()),
            ColumnJustification.NONE,
        )
        col_min_volume = StringColumn(
            "Temp Min Volume ({})".format(self._altcoin_trade_currency()),
            ColumnJustification.NONE,
        )
        col_trigger_price = self._altcoin_trigger_price_column()

        # Populate columns with offer info.

        for offer in offers:
            if col_enabled:
                col_enabled.add_row(self._to_enabled(offer))

            self.col_direction.add_row(self._direction_format(offer))
            col_btc_price.add_row(offer.price)
            self.col_amount.add_row(offer.amount)
            self.col_min_amount.add_row(offer.min_amount)
            col_volume.add_row(offer.volume)
            col_min_volume.add_row(offer.min_volume)

            if col_trigger_price:
                col_trigger_price.add_row(
                    self._to_blank_or_non_zero_value(offer.trigger_price)
                )

            self.col_payment_method.add_row(offer.payment_method_short_name)
            self.col_create_date.add_row(offer.date)
            self.col_offer_id.add_row(offer.id)

        amount_range = self._zipped_amount_range_columns()
        volume_range = ZippedStringColumns(
            TableBuilderConstants.COL_HEADER_VOLUME_RANGE.format(
                self._altcoin_trade_currency()
            ),
            ColumnJustification.RIGHT,
            " - ",
            col_min_volume.as_string_column(),
            col_volume.as_string_column(),
        )

        # Define and return the table instance with populated columns.

        if self._is_showing_my_offers():
            if self._is_showing_bsq_offers():
                return Table(
                    col_enabled.as_string_column(),
                    self.col_direction,
                    col_btc_price.justify(),
                    amount_range.as_string_column(
                        ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                    ),
                    volume_range.as_string_column(
                        ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                    ),
                    self.col_payment_method,
                    self.col_create_date.as_string_column(),
                    self.col_offer_id,
                )
            else:
                return Table(
                    col_enabled.as_string_column(),
                    self.col_direction,
                    col_btc_price.justify(),
                    amount_range.as_string_column(
                        ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                    ),
                    volume_range.as_string_column(
                        ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                    ),
                    col_trigger_price.justify(),
                    self.col_payment_method,
                    self.col_create_date.as_string_column(),
                    self.col_offer_id,
                )
        else:
            return Table(
                self.col_direction,
                col_btc_price.justify(),
                amount_range.as_string_column(
                    ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                ),
                volume_range.as_string_column(
                    ZippedStringColumns.DUPLICATION_MODE.EXCLUDE_DUPLICATES
                ),
                self.col_payment_method,
                self.col_create_date.as_string_column(),
                self.col_offer_id,
            )

    def _to_blank_or_non_zero_value(s: str) -> str:
        return "" if s.strip() == "0" else s

    def _first_offer_in_list(self) -> grpc_pb2.OfferInfo:
        return self.protos[0]

    def _is_showing_my_offers(self) -> bool:
        return self._first_offer_in_list().is_my_offer

    def _is_showing_fiat_offers(self) -> bool:
        return self.is_fiat_offer(self._first_offer_in_list())

    def _fiat_trade_currency(self) -> str:
        return self._first_offer_in_list().counter_currency_code

    def _altcoin_trade_currency(self) -> str:
        return self._first_offer_in_list().base_currency_code

    def _is_showing_bsq_offers(self) -> bool:
        return (
            not self.is_fiat_offer(self._first_offer_in_list())
            and self._altcoin_trade_currency() == "BSQ"
        )

    # Not a boolean column: YES, NO, or PENDING.
    def _enabled_column(self) -> Optional[StringColumn]:
        if self._is_showing_my_offers():
            return StringColumn(
                TableBuilderConstants.COL_HEADER_ENABLED, ColumnJustification.LEFT
            )
        return None

    def _fiat_trigger_price_column(self) -> Optional[StringColumn]:
        if self._is_showing_my_offers():
            return StringColumn(
                TableBuilderConstants.COL_HEADER_TRIGGER_PRICE.format(
                    self._fiat_trade_currency()
                ),
                ColumnJustification.RIGHT,
            )
        return None

    def _altcoin_trigger_price_column(self) -> Optional[StringColumn]:
        if self._is_showing_my_offers() and not self._is_showing_bsq_offers():
            return StringColumn(
                TableBuilderConstants.COL_HEADER_TRIGGER_PRICE.format(
                    self._altcoin_trade_currency()
                ),
                ColumnJustification.RIGHT,
            )
        return None

    def _to_enabled(self, offer: grpc_pb2.OfferInfo) -> str:
        if offer.is_my_offer and offer.is_my_pending_offer:
            return "PENDING"
        else:
            return "YES" if offer.is_activated else "NO"

    def _to_mirrored_direction(self, direction: str) -> str:
        return "SELL" if direction.upper() == "BUY" else "BUY"

    def _direction_format(self, offer: grpc_pb2.OfferInfo) -> str:
        if self.is_fiat_offer(offer):
            return offer.base_currency_code
        else:
            # Return "Sell BSQ (Buy BTC)", or "Buy BSQ (Sell BTC)".
            direction = offer.direction
            mirrored_direction = self._to_mirrored_direction(direction)
            return "{} {} ({} {})".format(
                mirrored_direction.capitalize(),
                offer.base_currency_code,
                direction.capitalize(),
                offer.counter_currency_code,
            )

    def _zipped_amount_range_columns(self) -> "ZippedStringColumns":
        if self.col_min_amount.is_empty or self.col_amount.is_empty:
            raise IllegalStateException("amount columns must have data")

        return ZippedStringColumns(
            TableBuilderConstants.COL_HEADER_AMOUNT_RANGE,
            ColumnJustification.RIGHT,
            " - ",
            self.col_min_amount.as_string_column(),
            self.col_amount.as_string_column(),
        )
