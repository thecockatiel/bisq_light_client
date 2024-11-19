from abc import ABC, abstractmethod
from concurrent.futures import Future
from datetime import timedelta, datetime 
from typing import Optional
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.file_transfer_part import FileTransferPart
from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.common.setup.log_setup import get_logger
from utils.formatting import get_short_id
from utils.time import get_time_ms

logger = get_logger(__name__)

class FileTransferSession(MessageListener, ABC):
    FTP_SESSION_TIMEOUT_MILLIS = int(timedelta(seconds=60).total_seconds()*1000)
    FILE_BLOCK_SIZE = Connection.PERMITTED_MESSAGE_SIZE - 1024

    class FtpCallback(ABC):
        @abstractmethod
        def on_ftp_progress(self, progress_pct: float) -> None:
            pass

        @abstractmethod
        def on_ftp_complete(self, session: 'FileTransferSession') -> None:
            pass

        @abstractmethod
        def on_ftp_timeout(self, status_msg: str, session: 'FileTransferSession') -> None:
            pass

    def __init__(self, network_node: NetworkNode,
                 peer_node_address: NodeAddress,
                 trade_id: str,
                 trader_id: int,
                 trader_role: str,
                 callback: Optional[FtpCallback] = None):
        self.network_node = network_node # for sending network messages
        self.peer_node_address = peer_node_address
        self.full_trade_id = trade_id
        self.trader_id = trader_id
        self.ftp_callback = callback
        self.zip_id = f"{get_short_id(self.full_trade_id)}_{trader_role.upper()}_" \
                     f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.data_awaiting_ack: Optional[FileTransferPart] = None
        self.file_offset_bytes = 0
        self.current_block_seq_num = -1
        self.expected_file_length = 0
        self.last_activity_time = 0
        self.reset_session()

    def reset_session(self) -> None:
        self.data_awaiting_ack = None
        self.file_offset_bytes = 0
        self.current_block_seq_num = -1
        self.expected_file_length = 0
        self.last_activity_time = 0
        self.network_node.remove_message_listener(self)
        logger.info("Ftp session parameters have been reset.")

    def on_message(self, network_envelope, connection):
        from bisq.core.support.dispute.mediation.file_transfer_receiver import FileTransferReceiver
        from bisq.core.support.dispute.mediation.file_transfer_sender import FileTransferSender
        
        if isinstance(network_envelope, FileTransferPart):
            # mediator receiving log file data
            ftp = network_envelope
            if isinstance(self, FileTransferReceiver):
                self.process_file_part_received(ftp)
        elif isinstance(network_envelope, AckMessage):
            ack_message = network_envelope
            if ack_message.source_type == AckMessageSourceType.LOG_TRANSFER:
                if ack_message.success:
                    logger.info(f"Received AckMessage for {ack_message.source_msg_class_name} with id {ack_message.source_id} and uid {ack_message.source_uid}")
                    if isinstance(self, FileTransferSender):
                        self.process_ack_for_file_part(ack_message.source_uid)
                else:
                    logger.warning(f"Received AckMessage with error state for {ack_message.source_msg_class_name} with id {ack_message.source_id} and errorMessage={ack_message.error_message}")

    def checkpoint_last_activity(self):
        self.last_activity_time = get_time_ms()

    @property
    def transfer_is_in_progress(self):
        return self.file_offset_bytes != self.expected_file_length

    def _session_timer_handler(self):
        if not self.transfer_is_in_progress: 
            # transfer may have finished before this timer executes
            return
        if get_time_ms() - self.last_activity_time < self.FTP_SESSION_TIMEOUT_MILLIS:
            logger.info(f"Last activity was {datetime.fromtimestamp(self.last_activity_time / 1000)}, we have not yet timed out.")
            self.init_session_timer()
        else:
            logger.warning(f"File transfer session timed out. expected: {self.expected_file_length} received: {self.file_offset_bytes}")
            if self.ftp_callback:
                self.ftp_callback.on_ftp_timeout("Timed out during send")
    
    def init_session_timer(self):
        UserThread.run_after(self._session_timer_handler, timedelta(milliseconds=self.FTP_SESSION_TIMEOUT_MILLIS/4)) # check more frequently than the timeout
        
    def _on_send_message_finished(self, future: Future, message: NetworkEnvelope, node_address: NodeAddress):
        try:
            future.result()
        except Exception as e:
            error_send = (f"Sending {message.__class__.__name__} "
                         f"to {node_address.get_full_address()} "
                         f"failed. That is expected if the peer is offline.\n\t"
                         f".\n\tException={str(e)}")
            logger.warning(error_send)
            if self.ftp_callback:
                self.ftp_callback.on_ftp_timeout("Peer offline", self)
            self.reset_session()
    
    def send_message(self, message: NetworkEnvelope, network_node: NetworkNode, node_address: NodeAddress):
        future = network_node.send_message(node_address, message)
        future.add_done_callback(lambda f: self._on_send_message_finished(f, message, node_address))
