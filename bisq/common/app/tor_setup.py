from bisq.common.file.file_util import delete_directory
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from pathlib import Path
from typing import Optional, Callable
from bisq.common.setup.log_setup import get_ctx_logger

from utils.dir import check_dir


class TorSetup:
    def __init__(self, tor_dir: Path = None):
        self.logger = get_ctx_logger(__name__)
        self.tor_dir = check_dir(tor_dir)

    # Should only be called if needed. Slows down Tor startup from about 5 sec. to 30 sec. if it gets deleted.
    def cleanup_tor_files(
        self,
        result_handler: Optional[Callable] = None,
        error_message_handler: Optional[ErrorMessageHandler] = None,
    ) -> None:
        """Should only be called if needed. Slows down Tor startup from about 5 sec. to 30 sec. if it gets deleted."""

        hidden_service = self.tor_dir.joinpath("hiddenservice")
        try:
            delete_directory(self.tor_dir, hidden_service, True)
            self.logger.info("All Tor files except hiddenservice directory got deleted")
            if result_handler:
                result_handler()
        except Exception as e:
            self.logger.error("cleanup_tor_files failed", exc_info=e)
            if error_message_handler:
                error_message_handler(str(e))
