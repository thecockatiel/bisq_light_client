from datetime import timedelta
from pathlib import Path
from typing import Optional
import zipfile
import uuid
from bisq.common.file.file_util import does_file_contain_keyword
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.file_transfer_part import FileTransferPart
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.mediation.file_transfer_session import FileTransferSession
from bisq.core.user.user import User


class FileTransferSender(FileTransferSession):

    def __init__(
        self,
        network_node: NetworkNode,
        peer_node_address: NodeAddress,
        trade_id: str,
        trader_id: int,
        trader_role: str,
        user: "User",
        callback: Optional[FileTransferSession.FtpCallback] = None,
        is_test: bool = False,
    ):
        super().__init__(
            network_node, peer_node_address, trade_id, trader_id, trader_role, callback
        )
        self.logger = get_ctx_logger(__name__)
        self._user = user
        self.zip_file_path = self._user.data_dir.joinpath(self.zip_id + ".zip")
        self.is_test = is_test
    
    def create_zip_file_to_send(self):
        self.create_zip_file_of_logs(self.zip_file_path, self.zip_id, self.full_trade_id)
        
    def create_zip_file_of_logs(self, zip_file_path: Path, zip_id: str, trade_id: str):
        try:
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Get all .log files in app data directory
                log_files = [f for f in self._user.data_dir.iterdir() if f.is_file()]
                
                for log_file in log_files:
                    filename = log_file.name
                     # always include bisq.log; and other .log files if they contain the TradeId
                    if (filename == "bisq.log" or
                            (trade_id is None and filename.endswith('.log')) or
                            (filename.endswith('.log') and does_file_contain_keyword(log_file, trade_id))):
                        
                        archive_path = f"{zip_id}/{filename}"
                        self.logger.info(f"Adding {filename} to zip file {zip_file_path}")
                        zipf.write(log_file, archive_path)
        except Exception as ex:
            self.logger.error(f"Error creating zip file: {str(ex)}", exc_info=ex)
            raise

    def init_send(self):
        self.init_session_timer()
        self.network_node.add_message_listener(self)
        
        # Get file size
        file_size = self.zip_file_path.stat().st_size
        self.expected_file_length = file_size
        
        # an empty block is sent as request to initiate file transfer, peer must ACK for transfer to continue
        self.data_awaiting_ack = FileTransferPart(
            self.network_node.node_address_property.value,
            self.full_trade_id,
            self.trader_id,
            str(uuid.uuid4()),
            self.expected_file_length,
            bytes()
        )
        
        self.upload_data()

    
    def send_next_block(self):
        if self.data_awaiting_ack is not None:
            error_msg = "prep_next_block_to_send invoked, but we are still waiting for a previous ACK"
            self.logger.warning(error_msg)
            raise RuntimeError(error_msg)

        with open(self.zip_file_path, "rb") as file:
            file.seek(self.file_offset_bytes)
            buff = file.read(self.FILE_BLOCK_SIZE)

        if not buff:  # EOF reached
            self.logger.info(f"Success! We have reached the EOF, {self.file_offset_bytes} bytes sent. Removing zip file {self.zip_file_path}")
            self.zip_file_path.unlink(True)
            if self.ftp_callback:
                self.ftp_callback.on_ftp_complete(self)
            UserThread.run_after(self.reset_session, timedelta(seconds=1))
            return

        self.data_awaiting_ack = FileTransferPart(
            self.network_node.node_address_property.value,
            self.full_trade_id,
            self.trader_id,
            str(uuid.uuid4()),
            self.current_block_seq_num,
            buff
        )
        
        self.upload_data()

    def retry_send(self):
        if self.transfer_is_in_progress:
            self.logger.info("Retry send of current block")
            self.init_session_timer()
            self.upload_data()
        else:
            def timeout_callback():
                if self.ftp_callback:
                    self.ftp_callback.on_ftp_timeout("Could not re-send", self)
            UserThread.run_after(timeout_callback, timedelta(seconds=1))

    def upload_data(self):
        if self.data_awaiting_ack is None:
            return
        
        ftp = self.data_awaiting_ack
        self.logger.info(f"Send FileTransferPart seq {ftp.seq_num_or_file_length} length {len(ftp.message_data)} to peer {self.peer_node_address}, UID={ftp.uid}")
        self.send_message(ftp, self.network_node, self.peer_node_address)

    def process_ack_for_file_part(self, ack_uid: str) -> bool:
        if self.data_awaiting_ack is None:
            self.logger.warning(f"We received an ACK we were not expecting. {ack_uid}")
            return False
            
        if self.data_awaiting_ack.uid != ack_uid:
            self.logger.warning("We received an ACK that has a different UID to what we were expecting. We ignore and wait for the correct ACK")
            self.logger.info(f"Received {ack_uid} expecting {self.data_awaiting_ack.uid}")
            return False
            
        # fileOffsetBytes gets incremented by the size of the block that was ack'd
        self.file_offset_bytes += len(self.data_awaiting_ack.message_data)
        self.current_block_seq_num += 1
        self.data_awaiting_ack = None
        self.checkpoint_last_activity()
        self.update_progress()
        
        if self.is_test:
            return True
            
        def send_next():
            try:
                self.send_next_block()
            except Exception as e:
                self.logger.error(str(e), exc_info=e)
                
        UserThread.run_after(send_next, timedelta(milliseconds=100)) # to trigger continuing the file transfer
        return True

    def update_progress(self):
        progress_pct = (self.file_offset_bytes / self.expected_file_length if self.expected_file_length > 0 else 0.0)
        if self.ftp_callback:
            self.ftp_callback.on_ftp_progress(progress_pct)
        self.logger.info(f"ftp progress: {progress_pct * 100:.0f}%")
