from typing import TYPE_CHECKING
from bisq.core.locale.currency_util import setup as CurrencyUtilSetup
from bisq.core.locale.res import Res
from bisq.core.setup.core_network_capabilities import CoreNetworkCapabilities

if TYPE_CHECKING:
    from bisq.common.config.config import Config


class CoreSetup:
    @staticmethod
    def setup(config: "Config"):
        CoreNetworkCapabilities.set_supported_capabilities(config)
        Res.setup()
        CurrencyUtilSetup()
