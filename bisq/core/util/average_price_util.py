from datetime import datetime, timedelta
from bisq.core.monetary.price import Price
from bisq.core.trade.statistics.trade_statistics_manager import TradeStatisticsManager
from bisq.core.user.preferences import Preferences 


# TODO: implement if needed

# AveragePriceUtil

_HOW_MANY_STD_DEVS_CONSTITUTE_OUTLIER = 10.0

def get_average_price_tuple(preferences: "Preferences", trade_statistics_manager: "TradeStatisticsManager", days: int, date: datetime = None) -> tuple[Price, Price]:
    if date is None:
        date = datetime.now()
    
    past_x_days = date - timedelta(days=days)
    raise NotImplementedError("get_average_price_tuple not implemented yet.")
    