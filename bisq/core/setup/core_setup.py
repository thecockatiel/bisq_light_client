from bisq.core.locale.currency_util import setup as CurrencyUtilSetup
from bisq.core.setup.core_network_capabilities import CoreNetworkCapabilities

class CoreSetup():
    @staticmethod
    def setup():
        CoreNetworkCapabilities.set_supported_capabilities()
        # TODO: Res setup ?
        CurrencyUtilSetup()