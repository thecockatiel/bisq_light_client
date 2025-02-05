from abc import ABC, abstractmethod
from bisq.cli.table.builder.table_type import TableType
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
import grpc_pb2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.cli.table.table import Table


class AbstractTableBuilder(ABC):

    def __init__(self, table_type: TableType, protos: list):
        self.table_type = table_type
        self.protos = protos
        if not protos:
            raise IllegalArgumentException("cannot build a table without rows")

    @abstractmethod
    def build(self) -> "Table":
        pass

    def is_fiat_offer(self, offer_info: grpc_pb2.OfferInfo) -> bool:
        return offer_info.base_currency_code == "BTC"
