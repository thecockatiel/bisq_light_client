
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
    
    def __init__(self, tor_dir: Optional[Path]) -> None:
        super().__init__()
        # tor_dir can be None if the user is providing the proxy and hidden service info
        self.tor_dir = tor_dir
        if self.tor_dir is not None:
            self.tor_dir.mkdir(parents=True, exist_ok=True)
            self.tor_dir.joinpath(".tor").mkdir(parents=True, exist_ok=True)
            """points to the place, where we will persist private key and address data"""
        
    @abstractmethod
    def get_tor(self) -> Future[Optional["Tor"]]:
        """returns none if we are connecting to limited running tor instance"""
        pass
    
    @abstractmethod
    def get_hidden_service_directory(self) -> Optional[Path]:
        """returns none if we are connecting to limited running tor instance"""
        pass
    
    def do_rolling_backup(self):
        """Do a rolling backup of the 'private_key' file. Does nothing if tor_dir is None (LimitedRunningTor)."""
        if self.tor_dir is not None:
            rolling_backup(self.tor_dir.joinpath(TorMode.HIDDEN_SERVICE_DIRECTORY), "private_key", 20)