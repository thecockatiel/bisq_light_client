import time
from collections import defaultdict
from typing import TYPE_CHECKING

from bisq.core.network.p2p.bundle_of_envelopes import BundleOfEnvelopes
from bisq.core.network.p2p.initial_data_request import InitialDataRequest
from bisq.core.network.p2p.initial_data_response import InitialDataResponse
from bisq.core.network.p2p.network.message_listener import MessageListener
from utils.formatting import format_duration_as_words, readable_file_size
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.network.connection_state import ConnectionState
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

class ConnectionStatistics(MessageListener):
    def __init__(self, connection: 'Connection', connection_state: 'ConnectionState'):
        self.connection = connection
        self.connection_state = connection_state
        self.sent_data_map = defaultdict(int)
        self.received_data_map = defaultdict(int)
        self.rrt_map = {} # type: dict[str, int]
        self.connection_creation_timestamp = get_time_ms()
        self.last_message_timestamp = self.connection_creation_timestamp
        self.time_on_send_msg = 0
        self.time_on_received_msg = 0
        self.sent_bytes = 0
        self.received_bytes = 0

        self.connection.add_message_listener(self)

    def shut_down(self):
        self.connection.remove_message_listener(self)

    def get_info(self):
        from bisq.core.network.p2p.network.inbound_connection import InboundConnection
        ls = "\n"
        now = get_time_ms()
        con_instance = "Inbound" if isinstance(self.connection, InboundConnection) else "Outbound"
        age = format_duration_as_words(now - self.connection_creation_timestamp)
        last_msg = format_duration_as_words(now - self.last_message_timestamp)
        peer = self.connection.peers_node_address.get_full_address() if self.connection.peers_node_address else "[address not known yet]"

        # For seeds its processing time, for peers rrt
        rrt = []
        for key, value in self.rrt_map.items():
            # Value is current milli as long we don't have the response
            if value < self.connection_creation_timestamp:
                formatted_key = key.replace("Request", "Request/Response")
                rrt.append(f"{formatted_key}: {format_duration_as_words(value)}")
            else:
                # we don't want to show pending requests
                rrt.append(f"{key} awaiting response... ")

        rrt_str = ", ".join(rrt)
        rrt_str = f"Time for response: [{rrt_str}]{ls}" if rrt else ""

        seed_node = self.connection_state.is_seed_node()
        info = (
            f"Age: {age}{ls}"
            f"Peer: {'[Seed node] ' if seed_node else ''}{peer}{ls}"
            f"Type: {self.connection_state.peer_type.name}{ls}"
            f"Direction: {con_instance}{ls}"
            f"UID: {self.connection.uid}{ls}"
            f"Time since last message: {last_msg}{ls}"
            f"{rrt_str}"
            f"Sent data: {readable_file_size(self.sent_bytes)}; {dict(self.sent_data_map)}{ls}"
            f"Received data: {readable_file_size(self.received_bytes)}; {dict(self.received_data_map)}{ls}"
            f"CPU time spent on sending messages: {format_duration_as_words(self.time_on_send_msg)}{ls}"
            f"CPU time spent on receiving messages: {format_duration_as_words(self.time_on_received_msg)}"
        )
        return info

    def on_message(self, network_envelope, connection):
        self.last_message_timestamp = get_time_ms()
        if isinstance(network_envelope, BundleOfEnvelopes):
            for envelope in network_envelope.envelopes:
                self.add_to_map(envelope, self.received_data_map)
            # We want to track also number of BundleOfEnvelopes 
            self.add_to_map(network_envelope, self.received_data_map)
        else:
            self.add_to_map(network_envelope, self.received_data_map)

    def on_message_sent(self, network_envelope, connection):
        self.last_message_timestamp = get_time_ms()
        if isinstance(network_envelope, BundleOfEnvelopes):
            for envelope in network_envelope.envelopes:
                self.add_to_map(envelope, self.sent_data_map)
            # We want to track also number of BundleOfEnvelopes
            self.add_to_map(network_envelope, self.sent_data_map)
        else:
            self.add_to_map(network_envelope, self.sent_data_map)

    def add_to_map(self, network_envelope: 'NetworkEnvelope', map_dict):
        key = network_envelope.__class__.__name__
        map_dict[key] += 1

        if isinstance(network_envelope, InitialDataRequest):
            self.rrt_map[key] = get_time_ms()
        elif isinstance(network_envelope, InitialDataResponse):
            associated_request = network_envelope.associated_request().__class__.__name__
            if associated_request in self.rrt_map:
                self.rrt_map[associated_request] = (get_time_ms()) - self.rrt_map[associated_request]

    def add_send_msg_metrics(self, time_spent, bytes_count):
        self.time_on_send_msg += time_spent
        self.sent_bytes += bytes_count

    def add_received_msg_metrics(self, time_spent, bytes_count):
        self.time_on_received_msg += time_spent
        self.received_bytes += bytes_count