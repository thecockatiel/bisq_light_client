import utils.aio
from bisq.common.setup.log_setup import (
    configure_logging,
    get_logger,
    set_custom_log_level,
)

from utils.tor import is_tor_socks_port_async, parse_tor_hidden_service_port
from utils.twisted import cancel_delayed_calls, wrap_with_ensure_deferred

configure_logging(None)
set_custom_log_level("TRACE")

import unittest as _unittest
from twisted.trial import unittest

from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode

logger = get_logger(__name__)

disabled = True


@_unittest.skipIf(disabled, "Disabled test because it requires an already running Tor instances")
class TestTorDetection(unittest.TestCase):
    
    def tearDown(self):
        cancel_delayed_calls()

    @wrap_with_ensure_deferred
    async def test_async_http_client_impl(self):
        result = await is_tor_socks_port_async("127.0.0.1", 9050)
        self.assertTrue(result)
        
class TestTorHiddenServiceUtils(unittest.TestCase):

    def test_parse_tor_hiddenservice_port(self):
        self.assertEqual(parse_tor_hidden_service_port("80"), (80, 80))
        self.assertEqual(parse_tor_hidden_service_port("80 9999"), (80, 9999))
        self.assertEqual(parse_tor_hidden_service_port("80 127.0.0.1:9999"), (80, 9999))


if __name__ == "__main__":
    _unittest.main()
