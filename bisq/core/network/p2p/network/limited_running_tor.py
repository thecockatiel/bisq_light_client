from bisq.common.setup.log_setup import get_ctx_logger
from utils.aio import as_future, get_asyncio_loop
import socket
import aiohttp
import asyncio
from bisq.core.network.p2p.network.tor_mode import TorMode
from pathlib import Path
from typing import Optional
from utils.time import get_time_ms
from aiohttp_socks import ProxyConnector, ProxyType


class LimitedRunningTor(TorMode):
    """
    This class only checks that the Tor instance is running and is possible to connect to it.
    
    User is responsible for starting the Tor instance and providing the hidden service info.
    """

    def __init__(
        self,
        proxy_host: str,
        proxy_port: int,
        hiddenservice_hostname: str,
        hiddenservice_port: int,
        hiddenservice_target_port: int = None,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ):
        super().__init__(None)
        self.logger = get_ctx_logger(__name__)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.hiddenservice_hostname = hiddenservice_hostname
        self.hiddenservice_port = hiddenservice_port
        self.hiddenservice_target_port = hiddenservice_target_port

    async def get_tor(self) -> None:
        ts1 = get_time_ms()
        retry_times = 3
        two_minutes_in_millis = 1000 * 60 * 2
        connected = False
        
        # Create unique validation token
        validation_token = f"tor_validation_{ts1}"
        
        proxy_connector = ProxyConnector(
            proxy_type=ProxyType.SOCKS5,
            host=self.proxy_host,
            port=self.proxy_port,
            username=self.proxy_username,
            password=self.proxy_password,
            rdns=True,
            ssl=False,
        )
        client_timeout = aiohttp.ClientTimeout(
            sock_connect=10,
            sock_read=10,
        )
        
        # Start server to receive validation request
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', self.hiddenservice_target_port))
        # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # commented out since somehow fixes the reuse issue.
        server.listen(5)
        server.setblocking(False)

        async def handle_validation_request():
            loop = get_asyncio_loop()
            while True:
                try:
                    client, _ = await loop.sock_accept(server)
                    client.setblocking(False)
                    request = await loop.sock_recv(client, 1024)
                    try:
                        if validation_token.encode() in request:
                            response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
                            await loop.sock_sendall(client, response)
                            return True
                    finally:
                        client.shutdown(socket.SHUT_RDWR)
                        client.close()
                except Exception as e:
                    self.logger.error(f"Error handling validation request: {str(e)}")
                    return False

        # Start validation request handler
        validation_task = as_future(handle_validation_request())
        exception = None
        
        async with aiohttp.ClientSession(connector=proxy_connector, timeout=client_timeout) as session:
            while not connected and retry_times > 0 and ((get_time_ms() - ts1) <= two_minutes_in_millis):
                try:
                    self.logger.info(f"Trying to connect to limited running tor proxy and hidden service. Attempt {4 - retry_times} of 3.")
                    async with session.get(
                        f"http://{self.hiddenservice_hostname}:{self.hiddenservice_port}/validate",
                        headers={"X-Validation-Token": validation_token}
                    ) as response:
                        if response.status == 200:
                            # Wait for validation request to be received
                            received = await validation_task
                            if received:
                                elapsed = get_time_ms() - ts1
                                self.logger.info(
                                    "\n################################################################\n"
                                    f"Tor proxy and hidden service validated successfully after {elapsed} ms."
                                    "\n################################################################"
                                )
                                connected = True

                except Exception as e:
                    retry_times -= 1
                    exception = e
                    await asyncio.sleep(1)

        server.shutdown(socket.SHUT_RDWR)
        server.close()
        if not connected:
            msg = "Couldn't validate already running tor proxy and hidden service after retrying 3 times."
            if exception:
                raise Exception(msg + f" Error: {exception}") from exception
            else:
                raise Exception(msg)

    def get_hidden_service_directory(self) -> Path:
        return None
