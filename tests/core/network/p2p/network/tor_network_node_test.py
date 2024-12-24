from bisq.core.network.p2p.network.message_listener import MessageListener
from utils.aio import as_future, get_asyncio_loop
from bisq.common.setup.log_setup import configure_logging, get_logger, set_custom_log_level
from utils.random import next_random_int
from pathlib import Path

from utils.test import run_with_reactor, teardown_reactor

# setup logging for this test
testdata_dir = Path(__file__).parent.joinpath("testdata")
testdata_dir.mkdir(parents=True, exist_ok=True)
configure_logging(testdata_dir.joinpath('test.log'))
set_custom_log_level("TRACE")

from bisq.core.network.p2p.network.bridge_address_provider import BridgeAddressProvider
from bisq.core.network.p2p.peers.keepalive.messages.ping import Ping
import unittest
import asyncio

import shutil
from twisted.internet import reactor

from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.network.p2p.network.setup_listener import SetupListener
from bisq.core.protocol.network.core_network_proto_resolver import CoreNetworkProtoResolver
from utils.clock import Clock

logger = get_logger(__name__)

disabled = True

@unittest.skipIf(disabled, "Disabled test because it requires running 2 Tor instances")
class TestTorNetworkNode(unittest.TestCase):
    def setUp(self):
        self.base_dir = testdata_dir.joinpath("nodes")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.tor_dir_1 = self.base_dir.joinpath("tor_dir_1")
        self.tor_dir_2 = self.base_dir.joinpath("tor_dir_2")
        
        logger.info(f"Testing Tor network node test base path: {self.base_dir}")
        
        class CustomBridgeAddressProvider(BridgeAddressProvider):
            def get_bridge_addresses(self):
                return [
                ]      
        
        # Create separate TorMode instances with different hidden service directories
        self.tor_mode1 = NewTor(self.base_dir, self.tor_dir_1, bridge_address_provider=CustomBridgeAddressProvider()) 
        self.tor_mode2 = NewTor(self.base_dir, self.tor_dir_2, bridge_address_provider=CustomBridgeAddressProvider()) 
        
        self.node1 = TorNetworkNode(
            service_port=80,
            network_proto_resolver=CoreNetworkProtoResolver(Clock()),
            tor_mode=self.tor_mode1,
            ban_filter=None,
            max_connections=10,
        )
        
        self.node2 = TorNetworkNode(
            service_port=80,
            network_proto_resolver=CoreNetworkProtoResolver(Clock()),
            tor_mode=self.tor_mode2,
            ban_filter=None,
            max_connections=10,
        )
        
        self.node1_ready = asyncio.Event()
        self.node2_ready = asyncio.Event()
        self.node1_received = asyncio.Event()
        self.node2_received = asyncio.Event()
        self.received_messages = []

    def tearDown(self):
        async def shutdown():
            # Cancel all pending calls
            teardown_reactor()
            # Shutdown nodes
            await asyncio.gather(
                self._shutdown_node(self.node1),
                self._shutdown_node(self.node2)
            )
            shutil.rmtree(self.base_dir)
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

    def create_message_listener(self, received_event: asyncio.Event):
        outer = self
        class TestMessageListener(MessageListener):
            def on_message(self, msg, connection):
                outer.received_messages.append(msg)
                received_event.set()
        return TestMessageListener()

    @run_with_reactor
    async def test_peer_communication(self):
        
        # Start both nodes
        await asyncio.gather(
                    self.node1.start(self.create_setup_listener(self.node1_ready)),
                    self.node2.start(self.create_setup_listener(self.node2_ready))
            )
        
        await asyncio.gather(
            self.node1_ready.wait(),
            self.node2_ready.wait()
        )
        
        # Setup message listeners
        self.node1.add_message_listener(self.create_message_listener(self.node1_received))
        self.node2.add_message_listener(self.create_message_listener(self.node2_received))
        
        # Get node addresses
        # node1_address = self.node1.node_address_property.get()
        node2_address = self.node2.node_address_property.get()
        
        # Connect nodes to each other
        retries = 0
        sent = False
        while not sent and retries < 3:
            try:
                await as_future(self.node1.send_message(node2_address, Ping(nonce=next_random_int(), last_round_trip_time=0)))
                sent = True
            except Exception as e:
                retries += 1
                logger.warning(f"TEST: send message failed ({e}). Retrying...")
        
        # Wait for messages to be received
        await self.node2_received.wait()
        
        # Verify messages
        self.assertTrue(len(self.received_messages) == 1)

if __name__ == '__main__':
    unittest.main()
    # TODO: check why test does not exit after shutdown
