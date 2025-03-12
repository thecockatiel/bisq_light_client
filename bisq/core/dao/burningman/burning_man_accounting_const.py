

from bisq.common.config.config import Config
from utils.python_helpers import classproperty


class BurningManAccountingConst:
    # now 763195 -> 107159 blocks takes about 14h
    # First tx at BM address 656036 Sun Nov 08 19:02:18 EST 2020
    # 2 months ago 754555 (date of comment = 2022-11-22)
    @classproperty
    def EARLIEST_BLOCK_HEIGHT(cls):
        return 111 if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest() else 656035

    EARLIEST_DATE_YEAR = 2020
    EARLIEST_DATE_MONTH = (
        11  # in java its 10 because it starts from 0, but in python it starts from 1
    )
    HIST_BSQ_PRICE_LAST_DATE_YEAR = 2022
    HIST_BSQ_PRICE_LAST_DATE_MONTH = (
        11  # in java its 10 because it starts from 0, but in python it starts from 1
    )
