from pathlib import Path
import socket
from typing import TYPE_CHECKING, Optional
from twisted.internet import reactor
from txtorcon import FilesystemOnionService, IOnionService, TorOnionAddress

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

    def __init__(self, local_port: int, hidden_service_dir: str, hidden_service_port: int, tor_network_node: "TorNetworkNode"):
        self._local_port = local_port
        self._hidden_service_dir = hidden_service_dir
        self._hidden_service_port = hidden_service_port
        self._tor_network_node = tor_network_node
        self._server_socket: Optional[socket.socket] = None
        # set after initialize
        self._onion_service: Optional["FilesystemOnionService"] = None
        
    async def initialize(self) -> "OnionIListeningPort":
        # ensure hs parent dir perm be 700
        self._tor_network_node.tor_mode.get_hidden_service_directory().parent.chmod(0o700) # same as self.tor_dir, but more explicit.
        
        # find if we are already running this hidden service and on which port it was listening before, so we can reuse it.
        found_hidden_service = None
        for hidden_service in self._tor_network_node.tor._config.HiddenServices:
            if Path(hidden_service.dir) == Path(self._hidden_service_dir):
                found_hidden_service = hidden_service
                # example of found_hidden_service.ports: ['9999 127.0.0.1:62442']
                self._local_port = int(found_hidden_service.ports[0].split(':')[1])
                logger.info(f"Hidden service was already published ({found_hidden_service.ports[0]}), adjusting local port to listen on that port.")
                break
        
        self._server_socket = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', self._local_port))
        sock.listen(5)
        
        if not found_hidden_service:
            progress_updates=lambda percent, tag, summary: logger.trace(f"Tor Hidden Service: {percent}%: {tag} - {summary}")
            # NOTE: this is probably a brittle way to create a hidden service, but it's the simplest way to do it for now.
            self._onion_service: "FilesystemOnionService"  = await as_future(FilesystemOnionService.create(
                reactor,
                self._tor_network_node.tor._config,
                self._hidden_service_dir,
                ['%d 127.0.0.1:%d' % (self._hidden_service_port, self._local_port)],
                version=3,
                progress=progress_updates,
            ))
        else:
            self._onion_service = found_hidden_service
        
    @property
    def server_socket(self):
        return self._server_socket
    
    @property
    def service_name(self):
        return self._onion_service.hostname
    
    @property
    def hidden_service_port(self):
        return self._hidden_service_port
        
    def __str__(self) -> str:
        return f"HiddenServiceSocket(local_port={self._local_port}, hidden_service_dir={self._hidden_service_dir}, hidden_service_port={self._hidden_service_port}, onion_uri={self.service_name})"
    
    async def close(self):
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
