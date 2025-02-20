from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Union
from bisq.core.monetary.price import Price

if TYPE_CHECKING:
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.user.preferences import Preferences


# TODO: implement if needed

# AveragePriceUtil

_HOW_MANY_STD_DEVS_CONSTITUTE_OUTLIER = 10.0


def get_average_price_tuple(
    preferences: "Preferences",
    trade_statistics_manager: "TradeStatisticsManager",
    past_days: Union[int, datetime],
    date: datetime = None,
) -> tuple[Price, Price]:
    if date is None:
        date = datetime.now()

    if isinstance(past_days, int):
        past_days = date - timedelta(days=past_days)
    else:
        past_days = past_days

    percent_to_trim = max(
        0, min(49, preferences.get_bsq_average_trim_threshold() * 100)
    )
    raise NotImplementedError("get_average_price_tuple not implemented yet.")
