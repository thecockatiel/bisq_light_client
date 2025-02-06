from typing import Any, Union
from collections.abc import Iterable
from bisq.cli.table.builder.abstract_table_builder import AbstractTableBuilder
from bisq.cli.table.builder.address_balance_table_builder import AddressBalanceTableBuilder
from bisq.cli.table.builder.bsq_balance_table_builder import BsqBalanceTableBuilder
from bisq.cli.table.builder.btc_balance_table_builder import BtcBalanceTableBuilder
from bisq.cli.table.builder.closed_trade_table_builder import ClosedTradeTableBuilder
from bisq.cli.table.builder.failed_trade_table_builder import FailedTradeTableBuilder
from bisq.cli.table.builder.offer_table_builder import OfferTableBuilder
from bisq.cli.table.builder.open_trade_table_builder import OpenTradeTableBuilder
from bisq.cli.table.builder.payment_account_table_builder import PaymentAccountTableBuilder
from bisq.cli.table.builder.table_type import TableType
from bisq.cli.table.builder.trade_detail_table_builder import TradeDetailTableBuilder
from bisq.cli.table.builder.transaction_table_builder import TransactionTableBuilder
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.custom_iterators import is_iterable

class TableBuilder(AbstractTableBuilder):
    def __init__(self, table_type: TableType, proto_or_protos: Union[Any, list]):
        super().__init__(
            table_type,
            list(proto_or_protos) if is_iterable(proto_or_protos) else [proto_or_protos],
        )

    def build(self):
        if self.table_type == TableType.ADDRESS_BALANCE_TBL:
            return AddressBalanceTableBuilder(self.protos).build()
        elif self.table_type == TableType.BSQ_BALANCE_TBL:
            return BsqBalanceTableBuilder(self.protos).build()
        elif self.table_type == TableType.BTC_BALANCE_TBL:
            return BtcBalanceTableBuilder(self.protos).build()
        elif self.table_type == TableType.CLOSED_TRADES_TBL:
            return ClosedTradeTableBuilder(self.protos).build()
        elif self.table_type == TableType.FAILED_TRADES_TBL:
            return FailedTradeTableBuilder(self.protos).build()
        elif self.table_type == TableType.OFFER_TBL:
            return OfferTableBuilder(self.protos).build()
        elif self.table_type == TableType.OPEN_TRADES_TBL:
            return OpenTradeTableBuilder(self.protos).build()
        elif self.table_type == TableType.PAYMENT_ACCOUNT_TBL:
            return PaymentAccountTableBuilder(self.protos).build()
        elif self.table_type == TableType.TRADE_DETAIL_TBL:
            return TradeDetailTableBuilder(self.protos).build()
        elif self.table_type == TableType.TRANSACTION_TBL:
            return TransactionTableBuilder(self.protos).build()
        else:
            raise IllegalArgumentException(
                f"invalid cli table type {getattr(self.table_type, 'name', self.table_type)}"
            )
