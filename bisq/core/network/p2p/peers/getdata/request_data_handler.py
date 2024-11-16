from concurrent.futures import Future
from datetime import timedelta
import random
import threading
from typing import TYPE_CHECKING, Optional

from bisq.core.common.timer import Timer
from bisq.core.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.peers.getdata.messages.get_data_request import GetDataRequest
from bisq.core.network.p2p.peers.getdata.messages.get_data_response import GetDataResponse
from bisq.log_setup import get_logger
from utils.formatting import readable_file_size
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.common.protocol.network.network_payload import NetworkPayload
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage

logger = get_logger(__name__)


class RequestDataHandler(MessageListener):
    TIMEOUT = 240
    
    class Listener:
        def on_complete(self, was_truncated: bool):
            pass

        def on_fault(self, error_message: str, connection: Optional["Connection"]):
            pass

    def __init__(
        self,
        network_node: "NetworkNode",
        data_storage: "P2PDataStorage",
        peer_manager: "PeerManager",
        listener: "Listener",
    ):
        self.network_node = network_node
        self.data_storage = data_storage
        self.peer_manager = peer_manager
        self.listener = listener
        self.timeout_timer: Optional[Timer] = None
        self.nonce = random.randint(-(2**31), 2**31 - 1)
        self.stopped = False
        self.peers_node_address: Optional["NodeAddress"] = None
        self.get_data_request_type = ""

    def cancel(self):
        self.cleanup()

    def request_data(
        self, node_address: "NodeAddress", is_preliminary_data_request: bool
    ):
        self.peers_node_address = node_address
        if not self.stopped:
            if is_preliminary_data_request:
                get_data_request = self.data_storage.build_preliminary_get_data_request(
                    self.nonce
                )
            else:
                get_data_request = self.data_storage.build_get_updated_data_request(
                    self.network_node.node_address.value, self.nonce
                )

            if self.timeout_timer is None:
                self.timeout_timer = UserThread.run_after(
                    lambda: self._handle_request_data_timeout(get_data_request, node_address),
                    timedelta(seconds=self.TIMEOUT),
                )

            self.get_data_request_type = get_data_request.__class__.__name__
            logger.info(
                f"\n\n>> We send a {self.get_data_request_type} to peer {node_address}\n"
            )
            self.network_node.add_message_listener(self)
            future = self.network_node.send_message(node_address, get_data_request)
            future.add_done_callback(lambda f: self._handle_request_data_done(f, node_address, get_data_request))
            

    def _handle_request_data_timeout(
        self, get_data_request: "GetDataRequest", node_address: "NodeAddress"
    ):
        if not self.stopped:
            error_message = f"A timeout occurred at sending getDataRequest: {get_data_request} on nodeAddress: {node_address}"
            logger.debug(f"{error_message} / RequestDataHandler={self}")
            self.handle_fault(
                error_message, node_address, CloseConnectionReason.SEND_MSG_TIMEOUT
            )
        else:
            logger.trace("We have stopped already. We ignore that timeoutTimer.run call. " +
                         "Might be caused by a previous networkNode.sendMessage.onFailure.")
            
    def _handle_request_data_done(self, future: Future["Connection"], node_address: "NodeAddress", get_data_request: "GetDataRequest"):
        try:
            connection = future.result()
            if connection is None:
                raise future.exception()
            if not self.stopped:
                logger.trace(f"Send {get_data_request} to {node_address} succeeded.")
            else:
                logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onSuccess call." +
                            "Might be caused by a previous timeout.")
        except Exception as e:
            if not self.stopped:
                message = "Sending getDataRequest to " + str(node_address) + \
                        " failed. That is expected if the peer is offline.\n\t" + \
                        "getDataRequest=" + str(get_data_request) + "." + \
                        "\n\tException=" + str(e)
                self.handle_fault(
                    message,
                    node_address,
                    CloseConnectionReason.SEND_MSG_FAILURE,
                )
            else:
                logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onFailure call. " +
                            "Might be caused by a previous timeout.")
                
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////       

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, GetDataResponse):
            if connection.peers_node_address == self.peers_node_address:
                if not self.stopped:
                    ts = get_time_ms()
                    get_data_response = network_envelope
                    self.log_contents(get_data_response)
                    if get_data_response.request_nonce == self.nonce:
                        self.stop_timeout_timer()
                        if not connection.peers_node_address:
                            logger.error("RequestDataHandler.onMessage: connection.peers_node_address must be present " +
                                    "at that moment")
                            return
                        self.data_storage.process_get_data_response(
                            get_data_response, connection.peers_node_address
                        )
                        self.cleanup()
                        self.listener.on_complete(get_data_response.was_truncated)
                    else:
                        logger.warning(
                            f"Nonce not matching. That can happen rarely if we get a response after a canceled " +
                                        "handshake (timeout causes connection close but peer might have sent a msg before " +
                                        "connection was closed).\n\t" +
                                        "We drop that message. nonce={self.nonce} / requestNonce={get_data_response.request_nonce}"
                        )
                    logger.info(
                        f"Processing GetDataResponse took {get_time_ms() - ts} ms"
                    )
                else:
                    logger.warning("We have stopped already. We ignore that onDataRequest call.")
            else:
                logger.debug("We got the message from another connection and ignore it on that handler. That is expected if we have several requests open.")

    def stop(self):
        self.cleanup()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def log_contents(self, get_data_response: "GetDataResponse"):
        data_set = get_data_response.data_set
        persistable_set = get_data_response.persistable_network_payload_set
        num_payloads: dict[str, tuple[int, int]] = {}
        for entry in data_set:
            class_name = entry.protected_storage_payload.__class__.__name__
            self.add_details(num_payloads, entry, class_name)
        for payload in persistable_set:
            class_name = payload.__class__.__name__
            self.add_details(num_payloads, payload, class_name)
        sb = "\n#################################################################\n"
        sb += f"Data provided by node: {self.peers_node_address.get_full_address()}\n"
        items = len(data_set) + len(persistable_set)
        sb += f"Received {items} instances from a {self.get_data_request_type}\n"
        for key, value in num_payloads.items():
            sb += f"{key}: {value[0]} / {readable_file_size(value[1])}\n"
        sb += "#################################################################\n"
        logger.info(sb)

    def add_details(
        self, num_payloads: dict[str, tuple[int, int]], network_payload: "NetworkPayload", class_name: str
    ):
        if class_name not in num_payloads:
            num_payloads[class_name] = (0, 0)
        num_payloads[class_name] = (
            num_payloads[class_name][0] + 1,
            # NOTE: following comment is for Java version of bisq. we need to benchmark this for python
            # toProtoMessage().getSerializedSize() is not very cheap. For about 1500 objects it takes about 20 ms
            # I think its justified to get accurate metrics but if it turns out to be a performance issue we might need
            # to remove it and use some more rough estimation by taking only the size of one data type and multiply it.
            num_payloads[class_name][1] + network_payload.to_proto_message().ByteSize(),
        )

    def handle_fault(
        self,
        error_message: str,
        node_address: "NodeAddress",
        reason: "CloseConnectionReason",
    ):
        self.cleanup()
        logger.info(error_message)
        self.peer_manager.handle_connection_fault(node_address=node_address)
        self.listener.on_fault(error_message, None)

    def cleanup(self):
        self.stopped = True
        self.network_node.remove_message_listener(self)
        self.stop_timeout_timer()

    def stop_timeout_timer(self):
        if self.timeout_timer:
            self.timeout_timer.stop()
            self.timeout_timer = None

    