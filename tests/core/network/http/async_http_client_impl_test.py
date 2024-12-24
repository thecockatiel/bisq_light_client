from utils.aio import get_asyncio_loop
from bisq.core.network.http.async_http_client_impl import AsyncHttpClientImpl
from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
import logging
from bisq.common.setup.log_setup import (
    configure_logging,
    get_logger,
    set_custom_log_level,
)
from pathlib import Path

from utils.test import run_with_reactor, teardown_reactor

# setup logging for this test
testdata_dir = Path(__file__).parent.joinpath(".testdata")
testdata_dir.mkdir(parents=True, exist_ok=True)
configure_logging(testdata_dir.joinpath("test.log"))
set_custom_log_level("TRACE")

from bisq.core.network.p2p.network.bridge_address_provider import BridgeAddressProvider
from bisq.core.network.p2p.peers.keepalive.messages.ping import Ping
import unittest
import asyncio

from twisted.internet import reactor

from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.network.p2p.network.setup_listener import SetupListener
from bisq.core.protocol.network.core_network_proto_resolver import (
    CoreNetworkProtoResolver,
)
from utils.clock import Clock

logger = get_logger(__name__)

disabled = True


@unittest.skipIf(disabled, "Disabled test because it requires running Tor instances")
class TestTorNetworkNode(unittest.TestCase):
    def setUp(self):
        self.base_dir = testdata_dir.joinpath("nodes")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.tor_dir_1 = self.base_dir.joinpath("tor_dir_1")

        logger.info(f"Testing Tor network node test base path: {self.base_dir}")

        class CustomBridgeAddressProvider(BridgeAddressProvider):
            def get_bridge_addresses(self):
                return [
                    #
                ]

        # Create separate TorMode instances with different hidden service directories
        self.tor_mode1 = NewTor(
            self.base_dir,
            self.tor_dir_1,
            bridge_address_provider=CustomBridgeAddressProvider(),
        )

        self.node1 = TorNetworkNode(
            service_port=80,
            network_proto_resolver=CoreNetworkProtoResolver(Clock()),
            tor_mode=self.tor_mode1,
            ban_filter=None,
            max_connections=10,
        )

        self.node1_ready = asyncio.Event()

    def tearDown(self):
        async def shutdown():
            # Cancel all pending calls
            teardown_reactor()
            # Shutdown nodes
            await asyncio.gather(
                self._shutdown_node(self.node1),
            )

        get_asyncio_loop().run_until_complete(shutdown())

    async def _shutdown_node(self, node: TorNetworkNode):
        shutdown_complete = asyncio.Event()
        node.shut_down(lambda: shutdown_complete.set())
        await shutdown_complete.wait()

    def create_setup_listener(self, ready_event: asyncio.Event):
        class TestSetupListener(SetupListener):
            def on_hidden_service_published(self_):
                ready_event.set()

            def on_setup_failed(self_, error):
                self.fail(f"Setup failed: {error}")

            def on_tor_node_ready(self_):
                pass

            def on_request_custom_bridges(self_):
                self.fail("Should not request custom bridges")

        return TestSetupListener()

    @run_with_reactor
    async def test_async_http_client_impl(self):

        # Start both nodes
        await asyncio.gather(
            self.node1.start(self.create_setup_listener(self.node1_ready)),
        )

        await asyncio.gather(
            self.node1_ready.wait(),
        )

        client = AsyncHttpClientImpl(
            base_url="http://runbtcpn7gmbj5rgqeyfyvepqokrijem6rbw7o5wgqbguimuoxrmcdyd.onion",
            socks5_proxy_provider=Socks5ProxyProvider(
                self.node1.socks_proxy.url, self.node1.socks_proxy.url
            ),
        )

        try:
            response = await client.get("/getAllMarketPrices")
        except Exception as e:
            self.fail(f"failed to request data: {e}")

        # Verify messages
        self.assertTrue(len(response) > 0)


if __name__ == "__main__":
    unittest.main()
