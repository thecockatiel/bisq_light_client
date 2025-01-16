import socket
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from utils.aio import get_asyncio_loop

if TYPE_CHECKING:
    from bisq.common.config.config import Config

logger = get_logger(__name__)


class LocalBitcoinNode:
    """
    Detects whether a Bitcoin node is running on localhost and contains logic for when to
    ignore it. The query methods lazily trigger the needed checks and cache the results.
    @see bisq.common.config.Config#ignoreLocalBtcNode
    """

    CONNECTION_TIMEOUT_SEC = 5.0

    def __init__(self, config: "Config"):
        self.config = config
        self.port = config.network_parameters.port
        self.detected: Optional[bool] = None

    async def should_be_used(self) -> bool:
        """
        Returns whether Bisq should use a local Bitcoin node, meaning that a node was
        detected and conditions under which it should be ignored have not been met. If
        the local node should be ignored, a call to this method will not trigger an
        unnecessary detection attempt.
        """
        return not self.should_be_ignored() and await self.is_detected()

    def should_be_ignored(self) -> bool:
        """
        Returns whether Bisq should ignore a local Bitcoin node even if it is usable.
        """
        base_currency_network = self.config.base_currency_network

        # For dao testnet (server side regtest) we disable the use of local bitcoin node
        # to avoid confusion if local btc node is not synced with our dao testnet master
        # node. Note: above comment was previously in WalletConfig::createPeerGroup.
        return (
            self.config.ignore_local_btc_node
            or base_currency_network.is_dao_regtest()
            or base_currency_network.is_dao_testnet()
        )

    async def is_detected(self) -> bool:
        """
        Returns whether a local Bitcoin node was detected. The check is triggered in case
        it has not been performed. No further monitoring is performed, so if the node
        goes up or down in the meantime, this method will continue to return its original
        value. See {@code MainViewModel#setupBtcNumPeersWatcher} to understand how
        disconnection and reconnection of the local Bitcoin node is actually handled.
        """
        if self.detected is None:
            self.detected = await self._detect(self.port)
        return self.detected

    @staticmethod
    async def _detect(port: int) -> bool:
        """
        Detect whether a Bitcoin node is running on localhost by attempting to connect
        to the node's port.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(LocalBitcoinNode.CONNECTION_TIMEOUT_SEC)
        sock.setblocking(False)
        try:
            await get_asyncio_loop().sock_connect(sock, ("127.0.0.1", port))
            logger.info(f"Local Bitcoin node detected on port {port}")
            return True
        except socket.error:
            logger.info(f"No local Bitcoin node detected on port {port}")
            return False
