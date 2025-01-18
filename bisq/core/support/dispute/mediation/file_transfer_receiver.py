from datetime import timedelta
from pathlib import Path
from typing import Optional
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.file_transfer_part import FileTransferPart
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.mediation.file_transfer_session import FileTransferSession
from bisq.common.setup.log_setup import get_logger

from global_container import GLOBAL_CONTAINER
from utils.formatting import get_short_id

logger = get_logger(__name__)

class FileTransferReceiver(FileTransferSession):

    def __init__(
        self,
        network_node: NetworkNode,
        peer_node_address: NodeAddress,
        trade_id: str,
        trader_id: int,
        trader_role: str,
        callback: Optional[FileTransferSession.FtpCallback] = None,
    ):
        super().__init__(
            network_node, peer_node_address, trade_id, trader_id, trader_role, callback
        )
        self.zip_file_path = self.ensure_receiving_directory_exists().joinpath(self.zip_id + ".zip")
    
    def process_file_part_received(self, ftp: FileTransferPart):
        self.checkpoint_last_activity()
        # check that the supplied sequence number is in line with what we are expecting
        if self.current_block_seq_num < 0:
            # we have not yet started receiving a file, validate this ftp packet as the initiation request
            self.init_receive_session(ftp.uid, ftp.seq_num_or_file_length)
        elif self.current_block_seq_num == ftp.seq_num_or_file_length:
            # we are in the middle of receiving a file; add the block of data to the file
            self.process_received_block(ftp, self.network_node, self.peer_node_address)
        else:
            logger.error(f"ftp sequence num mismatch, expected {self.current_block_seq_num} received {ftp.seq_num_or_file_length}")
            self.reset_session() # aborts the file transfer
    
    def init_receive_session(self, uid: str, expected_file_bytes: int):
        self.network_node.add_message_listener(self)
        self.expected_file_length = expected_file_bytes
        self.file_offset_bytes = 0
        self.current_block_seq_num = 0
        self.init_session_timer()
        logger.info(f"Received a start file transfer request, tradeId={self.full_trade_id}, traderId={self.trader_id}, size={self.expected_file_length}")
        logger.info(f"New file will be written to {self.zip_file_path}")
        UserThread.execute(lambda: self.ack_received_part(uid, self.network_node, self.peer_node_address))     
    
    def process_received_block(self, ftp: FileTransferPart, network_node: NetworkNode, peer_node_address: NodeAddress):
        try:
            with open(self.zip_file_path, "rb+" if self.zip_file_path.exists() else "wb+") as file:
                file.seek(self.file_offset_bytes)
                file.write(ftp.message_data)
                self.file_offset_bytes += len(ftp.message_data)
                logger.info(f"Sequence number {ftp.seq_num_or_file_length} for {get_short_id(ftp.trade_id)}, "
                          f"received data {self.file_offset_bytes} / {self.expected_file_length}")
                self.current_block_seq_num += 1
                
                def completion_check():
                    self.ack_received_part(ftp.uid, network_node, peer_node_address)
                    if self.file_offset_bytes >= self.expected_file_length:
                        logger.info(f"Success! We have reached the EOF, received {self.file_offset_bytes} "
                                  f"expected {self.expected_file_length}")
                        if self.ftp_callback:
                            self.ftp_callback.on_ftp_complete(self)
                        self.reset_session()

                UserThread.run_after(completion_check, timedelta(milliseconds=100))
        except IOError as e:
            logger.error(str(e), exc_info=e)

    def ack_received_part(self, uid: str, network_node: NetworkNode, peer_node_address: NodeAddress):
        ack_message = AckMessage(
            sender_node_address=peer_node_address,
            source_type=AckMessageSourceType.LOG_TRANSFER,
            source_msg_class_name=FileTransferPart.__name__,
            source_uid=uid,
            source_id=get_short_id(self.full_trade_id),
            success=True, 
            error_message=None
        )
        logger.info(f"Send AckMessage for {ack_message.source_msg_class_name} to peer {peer_node_address}. "
                   f"id={ack_message.source_id}, uid={ack_message.source_uid}")
        self.send_message(ack_message, network_node, peer_node_address)
        
    def ensure_receiving_directory_exists(self):
        receiving_directory = GLOBAL_CONTAINER.value.config.app_data_dir.joinpath("clientLogs")
        if not receiving_directory.exists():
            try:
                receiving_directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Could not create directory {receiving_directory.absolute()}: {e}")
                raise e
        
        return receiving_directory