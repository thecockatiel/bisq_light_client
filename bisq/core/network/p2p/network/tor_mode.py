
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from bisq.common.file.file_util import rolling_backup
from txtorcon import Tor
from asyncio import Future


class TorMode(ABC):
    """ 
    Holds information on how tor should be created and delivers a respective
    Tor object when asked.
    """

    HIDDEN_SERVICE_DIRECTORY = "hiddenservice"
    """
    The sub-directory where the private_key file sits in.
    """
    
    def __init__(self, tor_dir: Path) -> None:
        super().__init__()
        self.tor_dir = tor_dir
        self.tor_dir.mkdir(parents=True, exist_ok=True)
        self.tor_dir.joinpath(".tor").mkdir(parents=True, exist_ok=True)
        """points to the place, where we will persist private key and address data"""
        
    @abstractmethod
    def get_tor(self) -> Future[Optional["Tor"]]:
        pass
    
    @abstractmethod
    def get_hidden_service_directory(self) -> Path:
        pass
    
    def do_rolling_backup(self):
        """Do a rolling backup of the 'private_key' file."""
        rolling_backup(self.tor_dir.joinpath(TorMode.HIDDEN_SERVICE_DIRECTORY), "private_key", 20)