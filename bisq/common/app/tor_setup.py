from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from pathlib import Path
from typing import Optional, Callable
from bisq.common.config.config import CONFIG
import shutil
import logging

from utils.dir import check_dir

log = logging.getLogger(__name__)

class TorSetup:
    def __init__(self, tor_dir: Path = None):
        self.tor_dir = check_dir(tor_dir or CONFIG.tor_dir)

    def cleanup_tor_files(self, result_handler: Optional[Callable] = None,
                         error_message_handler: Optional[ErrorMessageHandler] = None) -> None:
        """Should only be called if needed. Slows down Tor startup from about 5 sec. to 30 sec. if it gets deleted."""
        try:
            hidden_service = self.tor_dir.joinpath("hiddenservice")
            if hidden_service.exists():
                shutil.rmtree(hidden_service)
            if result_handler:
                result_handler()
        except Exception as e:
            log.error(str(e), exc_info=e)
            if error_message_handler:
                error_message_handler(str(e))

