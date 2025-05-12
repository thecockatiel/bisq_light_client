from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Union
from bisq.common.util.math_utils import MathUtils
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3
from bisq.core.util.inlier_util import InlierUtil
from bitcoinj.base.utils.fiat import Fiat

if TYPE_CHECKING:
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.shared.preferences.preferences import Preferences

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
    all_trade_past_x_days = [
        trade
        for trade in trade_statistics_manager.observable_trade_statistics_set
        if past_days < trade.get_date() < date
    ]

    bsq_usd_all_trade_past_x_days = {
        True: [trade for trade in all_trade_past_x_days if trade.currency == "USD"],
        False: [trade for trade in all_trade_past_x_days if trade.currency == "BSQ"],
    }

    bsq_trade_past_x_days = (
        _remove_outliers(bsq_usd_all_trade_past_x_days[False], percent_to_trim)
        if percent_to_trim > 0
        else bsq_usd_all_trade_past_x_days[False]
    )

    usd_trade_past_x_days = (
        _remove_outliers(bsq_usd_all_trade_past_x_days[True], percent_to_trim)
        if percent_to_trim > 0
        else bsq_usd_all_trade_past_x_days[True]
    )

    usd_price = Price.value_of(
        "USD", _get_usd_average(bsq_trade_past_x_days, usd_trade_past_x_days)
    )
    bsq_price = Price.value_of("BSQ", _get_btc_average(bsq_trade_past_x_days))

    return usd_price, bsq_price


def _remove_outliers(
    trade_statistics_list: list[TradeStatistics3], percent_to_trim: float
) -> list[TradeStatistics3]:
    y_values = [item.price for item in trade_statistics_list if item.is_valid()]

    lower_bound, upper_bound = InlierUtil.find_inlier_range(
        y_values, percent_to_trim, _HOW_MANY_STD_DEVS_CONSTITUTE_OUTLIER
    )

    return [
        item
        for item in trade_statistics_list
        if lower_bound <= item.price <= upper_bound
    ]


def _get_btc_average(trade_statistics_list: list[TradeStatistics3]) -> int:
    accumulated_volume = 0
    accumulated_amount = 0

    for item in trade_statistics_list:
        accumulated_volume += item.get_trade_volume().value
        accumulated_amount += item.get_trade_amount().value  # Amount of BTC traded

    if accumulated_volume > 0:
        accumulated_amount_as_double = MathUtils.scale_up_by_power_of_10(
            accumulated_amount, Altcoin.SMALLEST_UNIT_EXPONENT
        )
        average_price = MathUtils.round_double_to_long(
            accumulated_amount_as_double / accumulated_volume
        )
    else:
        average_price = 0

    return average_price


def _get_usd_average(
    sorted_bsq_list: list[TradeStatistics3], sorted_usd_list: list[TradeStatistics3]
) -> int:
    # Use next USD/BTC print as price to calculate BSQ/USD rate
    # Store each trade as amount of USD and amount of BSQ traded
    usd_bsq_list = []
    usd_btc_price = (
        10000.0  # Default to 10000 USD per BTC if there is no USD feed at all
    )

    i = 0
    for item in sorted_bsq_list:
        # Find USD price for trade item
        while i < len(sorted_usd_list):
            usd = sorted_usd_list[i]
            if usd.date > item.date:
                usd_btc_price = MathUtils.scale_down_by_power_of_10(
                    usd.get_trade_price().value, Fiat.SMALLEST_UNIT_EXPONENT
                )
                break
            i += 1

        bsq_amount = MathUtils.scale_down_by_power_of_10(
            item.get_trade_volume().value, Altcoin.SMALLEST_UNIT_EXPONENT
        )
        btc_amount = MathUtils.scale_down_by_power_of_10(
            item.get_trade_amount().value, Altcoin.SMALLEST_UNIT_EXPONENT
        )
        usd_bsq_list.append((usd_btc_price * btc_amount, bsq_amount))

    usd_traded = sum(item[0] for item in usd_bsq_list)
    bsq_traded = sum(item[1] for item in usd_bsq_list)

    if bsq_traded > 0:
        average_as_double = usd_traded / bsq_traded
        average_scaled_up = MathUtils.scale_up_by_power_of_10(
            average_as_double, Fiat.SMALLEST_UNIT_EXPONENT
        )
        average_price = MathUtils.round_double_to_long(average_scaled_up)
    else:
        average_price = 0

    return average_price
