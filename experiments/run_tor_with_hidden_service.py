from utils.aio import as_future, get_asyncio_loop
import os
from txtorcon import FilesystemOnionService
import asyncio
from pathlib import Path
from bisq.common.setup.common_setup import CommonSetup
from bisq.common.setup.graceful_shutdown_handler import GracefulShutDownHandler
from bisq.core.network.p2p.network.hidden_service_socket import HiddenServiceSocket
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.network.utils.utils import Utils
from twisted.internet import reactor
from global_container import GLOBAL_CONTAINER
from twisted.internet.defer import Deferred

from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.common.setup.log_setup import configure_logging, get_logger

configure_logging(log_file=None, log_level=GLOBAL_CONTAINER.value.config.log_level)

logger = get_logger(__name__)

class MainApp(GracefulShutDownHandler):
    async def main(self):
        CommonSetup.setup_sig_int_handlers(self)
        base_dir = Path(__file__).parent.joinpath(".testdata")
        base_dir.mkdir(exist_ok=True, parents=True)
        tor_dir = base_dir.joinpath("tor")
        tor_dir.mkdir(exist_ok=True, parents=True)
        try:
            self.tor = await NewTor(
                base_dir,
                tor_dir,
                GLOBAL_CONTAINER.value.config.torrc_file,
                "SocksPort=9050,ControlPort=9052",
                None,
                True,
            ).get_tor()
            target_port = Utils.find_free_system_port()
            logger.info(f"initializing hidden service...")
            self._onion_service: "FilesystemOnionService" = await as_future(FilesystemOnionService.create(
                reactor,
                self.tor._config,
                str(tor_dir.joinpath("hiddenservice")),
                ['%d 127.0.0.1:%d' % (9999, target_port)],
                version=3,
            ))
            logger.info(f"hidden service initialized: {self._onion_service.hostname}:9999 -> {target_port}")
            await as_future(Deferred())
        except Exception as e:
            logger.error(f"Error while initializing tor and hidden service: {e}", exc_info=e)
            raise
        
    def graceful_shut_down(self, result_handler):
        # no need for gracefulness
        os._exit(0)
    
if __name__ == '__main__':
    app = MainApp()
    future = as_future(app.main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()