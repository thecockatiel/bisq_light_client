from typing import TYPE_CHECKING, Optional
import random
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.http.tx_broadcast_http_client import TxBroadcastHttpClient
from bisq.core.network.http.http_response_error import HttpResponseError

if TYPE_CHECKING:
    from bitcoinj.wallet.wallet import Wallet
    from bitcoinj.core.transaction import Transaction
    from bisq.common.config.config import Config
    from bisq.core.btc.nodes.local_bitcoin_node import LocalBitcoinNode
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.user.preferences import Preferences

logger = get_logger(__name__)

class MemPoolSpaceTxBroadcaster:
    socks5_proxy_provider = None
    preferences = None
    local_bitcoin_node = None
    config = None

    @classmethod
    def init(
        cls,
        socks5_proxy_provider: "Socks5ProxyProvider",
        preferences: "Preferences",
        local_bitcoin_node: "LocalBitcoinNode",
        config: "Config",
    ):
        cls.socks5_proxy_provider = socks5_proxy_provider
        cls.preferences = preferences
        cls.local_bitcoin_node = local_bitcoin_node
        cls.config = config

    @classmethod
    async def broadcast_tx(cls, tx: "Transaction", wallet: "Wallet") -> None:
        tx.maybe_finalize(wallet)

        if not cls.config.base_currency_network.is_mainnet():
            logger.info("MemPoolSpaceTxBroadcaster only supports mainnet")
            return
        
        if await cls.local_bitcoin_node.should_be_used():
            logger.info("A local Bitcoin node is detected and used. For privacy reasons we do not use the tx broadcast to mempool nodes in that case.")
            return
        
        if not cls.socks5_proxy_provider:
            logger.warning("We got broadcast_tx called before init was called.")
            return

        tx_id_to_send = tx.get_tx_id()
        raw_tx = tx.bitcoin_serialize().hex()
        
        tx_broadcast_services = list(cls.preferences.get_default_tx_broadcast_services())
        # Broadcast to first service
        service_address = await cls._attempt_to_broadcast_tx(tx_id_to_send, raw_tx, tx_broadcast_services)
        if service_address:
            # Broadcast to second service
            try:
                tx_broadcast_services.remove(service_address)
            except:
                pass
            await cls._attempt_to_broadcast_tx(tx_id_to_send, raw_tx, tx_broadcast_services)
        
        
    @classmethod
    async def _attempt_to_broadcast_tx(cls, tx_id_to_send: str, raw_tx: str, tx_broadcast_services: list[str]) -> Optional[str]:
        service_address = cls.get_random_service_address(tx_broadcast_services)
        if not service_address:
            logger.warning(f"We don't have a serviceAddress available. txBroadcastServices={tx_broadcast_services}")
            return
        await cls._broadcast_tx_to_service(service_address, tx_id_to_send, raw_tx)
        return service_address
    
    @classmethod
    async def _broadcast_tx_to_service(cls, service_address: str, tx_id_to_send: str, raw_tx: str) -> None:
        http_client = TxBroadcastHttpClient(service_address, cls.socks5_proxy_provider)
        http_client.ignore_socks5_proxy = False
        
        logger.info(f"We broadcast rawTx {raw_tx} to {service_address}")
        
        try:
            tx_id = await http_client.post(raw_tx)
            if tx_id == tx_id_to_send:
                logger.info(f"Broadcast of raw tx with txId {tx_id} to {service_address} was successful. rawTx={raw_tx}")
            else:
                logger.error(f"The txId we got returned from the service does not match our tx of the sending tx. txId={tx_id}; txIdToSend={tx_id_to_send}")
        except HttpResponseError as e:
            # See all error codes at: https://github.com/bitcoin/bitcoin/blob/master/src/rpc/protocol.h
            if e.status == 400 and "code\":-27" in e.response_text:
                logger.info(f"Broadcast of raw tx to {service_address} failed as transaction {tx_id_to_send} is already confirmed")
            else:
                logger.info(f"Broadcast of raw tx to {service_address} failed for transaction {tx_id_to_send}. status={e.status}, error={e.response_text}")
        except Exception as e:
            logger.warning(f"Broadcast of raw tx with txId {tx_id_to_send} to {service_address} failed. Error={str(e)}")
            
    @staticmethod
    def get_random_service_address(tx_broadcast_services: list[str]) -> Optional[str]:
        assert tx_broadcast_services is not None
        return random.choice(tx_broadcast_services) if tx_broadcast_services else None