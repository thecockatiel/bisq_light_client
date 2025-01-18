import os
from pathlib import Path
import socket
from typing import TYPE_CHECKING, Optional, cast
from twisted.internet import reactor
from txtorcon import FilesystemOnionService, IOnionService, Tor, TorOnionAddress

from utils.aio import as_future
from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
    
    

logger = get_logger(__name__)

class OnionIListeningPort:
    @property
    def onion_service() -> "IOnionService":
        pass 
    
    def getHost() -> "TorOnionAddress":
        pass

class HiddenServiceSocket:

    def __init__(self, local_port: int, hidden_service_dir: Optional[Path], hidden_service_port: int, tor_instance: "Tor"):
        self._local_port = local_port
        self._hidden_service_dir = hidden_service_dir
        self._hidden_service_port = hidden_service_port
        self._server_socket: Optional[socket.socket] = None
        self._tor_instance = tor_instance
        # set after initialize
        self._onion_service: Optional["FilesystemOnionService"] = None
        self._onion_hostname: str = None
        
    async def initialize(self) -> "OnionIListeningPort":
        found_hidden_service: Optional["FilesystemOnionService"] = None
        
        if self._tor_instance:
            if not self._hidden_service_dir:
                raise ValueError("Hidden service directory must also be provided when tor instance is provided.")
            # ensure hs parent dir perm be 700
            if not os.access(self._hidden_service_dir.parent, os.F_OK):
                self._hidden_service_dir.parent.chmod(0o700)
            
            # find if we are already running this hidden service and on which port it was listening before, so we can reuse it.
            for hidden_service in self._tor_instance._config.HiddenServices:
                if Path(hidden_service.dir) == self._hidden_service_dir:
                    found_hidden_service = cast(FilesystemOnionService, hidden_service)
                    # example of found_hidden_service.ports: ['9999 127.0.0.1:62442']
                    self._local_port = int(found_hidden_service.ports[0].split(':')[1])
                    logger.info(f"Hidden service was already published ({found_hidden_service.ports[0]}), adjusting local port to listen on that port.")
                    break
        
        self._server_socket = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setblocking(False)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allow reuse of port
        sock.bind(('127.0.0.1', self._local_port))
        sock.listen(5)
        
        if found_hidden_service:
            self._onion_service = found_hidden_service
            self._onion_hostname = self._onion_service.hostname
        elif self._tor_instance:
            progress_updates=lambda percent, tag, summary: logger.trace(f"Tor Hidden Service: {percent}%: {tag} - {summary}")
            # NOTE: this is probably a brittle way to create a hidden service, but it's the simplest way to do it for now.
            self._onion_service = cast(FilesystemOnionService, await as_future(FilesystemOnionService.create(
                reactor,
                self._tor_instance._config,
                str(self._hidden_service_dir),
                ['%d 127.0.0.1:%d' % (self._hidden_service_port, self._local_port)],
                version=3,
                progress=progress_updates,
            )))
            self._onion_hostname = self._onion_service.hostname
        else:
            logger.info(f"Hidden service is probably provided by user, skipping hidden service control.")
            
        
    @property
    def server_socket(self):
        return self._server_socket
    
    @property
    def service_name(self):
        return self._onion_hostname
    
    @property
    def hidden_service_port(self):
        return self._hidden_service_port
        
    def __str__(self) -> str:
        return f"HiddenServiceSocket(local_port={self._local_port}, hidden_service_dir={self._hidden_service_dir}, hidden_service_port={self._hidden_service_port}, onion_uri={self.service_name})"
    
    async def close(self):
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
