
from datetime import timedelta
from typing import TYPE_CHECKING, Optional

from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.bundle_of_envelopes import BundleOfEnvelopes
from bisq.core.network.p2p.initial_data_request import InitialDataRequest
from bisq.core.network.p2p.initial_data_response import InitialDataResponse
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.peer_type import PeerType
from bisq.core.network.p2p.prefixed_sealed_and_signed_message import PrefixedSealedAndSignedMessage
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection import Connection


class ConnectionState(MessageListener):
    # We protect the INITIAL_DATA_EXCHANGE PeerType for max. 4 minutes in case not all expected initialDataRequests
    # and initialDataResponses have not been all sent/received. In case the PeerManager need to close connections
    # if it exceeds its limits the connectionCreationTimeStamp and lastInitialDataExchangeMessageTimeStamp can be
    # used to set priorities for closing connections.
    PEER_RESET_TIMER_DELAY_SEC = 4 * 60  # 4 minutes
    COMPLETED_TIMER_DELAY_SEC = 10

    # We have 2 GetDataResponses and 3 GetHashResponses. If node is a lite node it also has a GetBlocksResponse if
    # blocks are missing.
    MIN_EXPECTED_RESPONSES = 5
    expected_initial_data_responses = MIN_EXPECTED_RESPONSES

    @staticmethod
    def increment_expected_initial_data_responses():
        # If app runs in LiteNode mode there is one more expected request for the getBlocks request, so we increment standard value.
        ConnectionState.expected_initial_data_responses += 1

    def __init__(self, connection: 'Connection'):
        self.logger = get_ctx_logger(__name__)
        self.connection = connection
        self.peer_type = PeerType.PEER
        self.num_initial_data_requests = 0
        self.num_initial_data_responses = 0
        self.last_initial_data_msg_timestamp = 0
        self.is_seed_node = False

        self.peer_type_reset_due_timeout_timer: Optional[Timer] = None
        self.initial_data_exchange_completed_timer: Optional[Timer] = None

        self.connection.add_message_listener(self)

    def shut_down(self):
        self.connection.remove_message_listener(self)
        self.stop_timer()

    def on_message(self, network_envelope, connection):
        if isinstance(network_envelope, BundleOfEnvelopes):
            for envelope in network_envelope.envelopes:
                self.on_message_sent_or_received(envelope)
        else:
            self.on_message_sent_or_received(network_envelope)

    def on_message_sent(self, network_envelope, connection):
        if isinstance(network_envelope, BundleOfEnvelopes):
            for envelope in network_envelope.envelopes:
                self.on_message_sent_or_received(envelope)
        else:
            self.on_message_sent_or_received(network_envelope)

    def on_message_sent_or_received(self, network_envelope: NetworkEnvelope):
        if isinstance(network_envelope, InitialDataRequest):
            self.num_initial_data_requests += 1
            self.on_initial_data_exchange()
        elif isinstance(network_envelope, InitialDataResponse):
            self.num_initial_data_responses += 1
            self.on_initial_data_exchange()
        elif isinstance(network_envelope, PrefixedSealedAndSignedMessage) and self.connection.peers_node_address:
            self.peer_type = PeerType.DIRECT_MSG_PEER

    def on_initial_data_exchange(self):
        # If we have a higher prio type we do not handle it
        if self.peer_type == PeerType.DIRECT_MSG_PEER:
            self.stop_timer()
            return

        self.peer_type = PeerType.INITIAL_DATA_EXCHANGE
        self.last_initial_data_msg_timestamp = get_time_ms()
        self.maybe_reset_initial_data_exchange_type()

        if self.peer_type_reset_due_timeout_timer is None:
            self.peer_type_reset_due_timeout_timer = UserThread.run_after(self.reset_initial_data_exchange_type, timedelta(seconds=self.PEER_RESET_TIMER_DELAY_SEC))

    def maybe_reset_initial_data_exchange_type(self):
        if self.num_initial_data_responses >= self.expected_initial_data_responses:
            # We have received the expected messages from initial data requests. We delay a bit the reset
            # to give time for processing the response and more tolerance to edge cases where we expect more responses.
            # Reset to PEER does not mean disconnection as well, but just that this connection has lower priority and
            # runs higher risk for getting disconnected.
            if self.initial_data_exchange_completed_timer is None:
                self.initial_data_exchange_completed_timer = UserThread.run_after(self.reset_initial_data_exchange_type, timedelta(seconds=self.COMPLETED_TIMER_DELAY_SEC))

    def reset_initial_data_exchange_type(self):
        # If we have a higher prio type we do not handle it
        if self.peer_type == PeerType.DIRECT_MSG_PEER:
            self.stop_timer()
            return

        self.stop_timer()
        self.peer_type = PeerType.PEER
        self.logger.info(f"We have changed the peerType from INITIAL_DATA_EXCHANGE to PEER as we have received all "
                    f"expected initial data responses at connection with peer {self.connection.peers_node_address}/{self.connection.uid}.")

    def stop_timer(self):
        if self.peer_type_reset_due_timeout_timer is not None:
            self.peer_type_reset_due_timeout_timer.stop()
            self.peer_type_reset_due_timeout_timer = None
        if self.initial_data_exchange_completed_timer is not None:
            self.initial_data_exchange_completed_timer.stop()
            self.initial_data_exchange_completed_timer = None

    def __str__(self):
        return (f"ConnectionState{{\n"
                f"     peerType={self.peer_type},\n"
                f"     numInitialDataRequests={self.num_initial_data_requests},\n"
                f"     numInitialDataResponses={self.num_initial_data_responses},\n"
                f"     lastInitialDataMsgTimeStamp={self.last_initial_data_msg_timestamp},\n"
                f"     isSeedNode={self.is_seed_node},\n"
                f"     expectedInitialDataResponses={self.expected_initial_data_responses}\n}}")