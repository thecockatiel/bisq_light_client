# TODO not essential so probably not gonna implement for now

from typing import TYPE_CHECKING
from utils.data import ObservableSet

if TYPE_CHECKING:
    from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3

class TradeStatisticsManager:

    def __init__(self):
        self.observable_trade_statistics_set = ObservableSet["TradeStatistics3"]()

    def shut_down(self):
        pass

    def on_all_services_initialized(self):
        pass

    def maybe_dump_statistics(self):
        pass

    def maybe_republish_trade_statistics(self):
        pass
