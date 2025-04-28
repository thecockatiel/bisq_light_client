from bisq.common.setup.log_setup import get_ctx_logger
from utils.aio import as_future
from txtorcon import Tor, connect
from bisq.core.network.p2p.network.tor_mode import TorMode
from pathlib import Path
from typing import Optional, cast
from utils.time import get_time_ms
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint



class RunningTor(TorMode):
    """
    This class creates a brand new instance of the Tor onion router.
    
    When asked, the class checks for the authentication method selected and
    connects to the given control port. Finally, a {@link Tor} instance is
    returned for further use.
    """

    def __init__(
        self,
        tor_dir: Path,
        control_host: str,
        control_port: int,
        password: str,
    ):
        super().__init__(tor_dir)
        self.logger = get_ctx_logger(__name__)
        self._control_host = control_host
        self._control_port = control_port
        self._password = password

    async def get_tor(self) -> Optional["Tor"]:
        ts1 = get_time_ms()
        retry_times = 3
        two_minutes_in_millis = 1000 * 60 * 2

        while retry_times > 0 and ((get_time_ms() - ts1) <= two_minutes_in_millis):
            
            try:
                self.logger.info("Connecting to running tor")
                
                get_password = lambda: self._password

                # txtorcon uses cookie automatically if it's available, then falls back to password if available
                result = await as_future(connect(
                    reactor,
                    TCP4ClientEndpoint(reactor, self._control_host, self._control_port),
                    get_password if self._password else None,
                ))
                result = cast(Tor, result)

                elapsed = get_time_ms() - ts1
                self.logger.info(
                    "\n################################################################\n"
                    f"Connecting to Tor successful after {elapsed} ms. Start publishing hidden service.\n"
                    "################################################################"
                )

                return result

            except Exception as e:
                retry_times -= 1
                self.logger.error("Couldn't connect to Tor.", exc_info=e)
                
        raise Exception("Couldn't connect to Tor after retrying 3 times.")

    def get_hidden_service_directory(self) -> Path:
        return self.tor_dir.joinpath(TorMode.HIDDEN_SERVICE_DIRECTORY)
