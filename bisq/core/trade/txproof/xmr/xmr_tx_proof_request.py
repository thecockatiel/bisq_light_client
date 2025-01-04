import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.trade.txproof.xmr.xmr_tx_proof_http_client import XmrTxProofHttpClient
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_detail import XmrTxProofRequestDetail
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_result import XmrTxProofRequestResult
from bisq.core.util.json_util import JsonUtil
from utils.aio import run_in_loop
from datetime import timedelta
from bisq.common.handlers.fault_handler import FaultHandler
from bisq.core.trade.txproof.asset_tx_proof_request import AssetTxProofRequest, AssetTxProofRequestResult
from bisq.core.trade.txproof.xmr.xmr_raw_tx_parser import XmrRawTxParser
from bisq.core.trade.txproof.xmr.xmr_tx_proof_parser import XmrTxProofParser
from utils.formatting import get_short_id
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.trade.txproof.xmr.xmr_tx_proof_model import XmrTxProofModel
    
logger = get_logger(__name__)

class XmrTxProofRequest(AssetTxProofRequest[AssetTxProofRequestResult]):
    """
    Requests for the XMR tx proof for a particular trade from a particular service.
    Repeats every 90 sec requests if tx is not confirmed or found yet until MAX_REQUEST_PERIOD of 12 hours is reached.
    """
    REPEAT_REQUEST_PERIOD = timedelta(milliseconds=90)
    MAX_REQUEST_PERIOD = timedelta(hours=12)
    
    def __init__(self, socks5_proxy_provider: "Socks5ProxyProvider", model: "XmrTxProofModel"):
        self.tx_proof_parser = XmrTxProofParser()
        self.raw_tx_parser = XmrRawTxParser()
        self.model = model
        
        self.http_client = XmrTxProofHttpClient(socks5_proxy_provider=socks5_proxy_provider)
        
        # many things regarding using proxy for urls or not is handled at http client level
        self.http_client.base_url = model.service_address
        
        self.terminated = False
        self.first_request = get_time_ms()
        self.result: Optional[XmrTxProofRequestResult] = None
        self.request_future: Optional["asyncio.Future[Optional[XmrTxProofRequestResult]]"] = None
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def request_from_service(self, result_handler: Callable[[XmrTxProofRequestResult], None], fault_handler: "FaultHandler"):
        if self.terminated:
            # the XmrTransferProofService has asked us to terminate i.e. not make any further api calls
            # this scenario may happen if a re-request is scheduled from the callback below
            logger.warning(f"Not starting {self} as we have already terminated.")
            return
        
        if self.http_client.has_pending_request:
            logger.warning(f"We have a pending request open. We ignore that request. httpClient {self.http_client}")
            return
        
        # Timeout handling is delegated to the connection timeout handling in httpClient.
        
        async def do_request():
            result = await self._get_result_from_raw_tx_request()
            if result != XmrTxProofRequestResult.SUCCESS:
                return result
            
            if self.terminated:
                return None
            
            # Only if the rawTx request succeeded we go on to the tx proof request.
            # The result from the rawTx request does not contain any detail data in the
            # success case, so we drop it.
            result = await self._get_result_from_tx_proof_request()
            return result
        
        self.request_future = future = run_in_loop(do_request())
        
        def on_done(f: asyncio.Future[Optional["XmrTxProofRequestResult"]]):
            try:
                self.result = result = f.result()
                
                if self.terminated:
                    logger.warning(f"We received {result} but {self} was terminated already. We do not process result.")
                    return
                
                match result:
                    case XmrTxProofRequestResult.PENDING:
                        if self._is_timeout_reached():
                            logger.warning(f"{self} took too long without a success or failure/error result We give up. "
                                           "Might be that the transaction was never published.")
                            # If we reached out timeout we return with an error.
                            UserThread.execute(lambda: result_handler(XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.NO_RESULTS_TIMEOUT)))
                        else:
                            UserThread.run_after(lambda: self.request_from_service(result_handler, fault_handler), XmrTxProofRequest.REPEAT_REQUEST_PERIOD)
                            # We update our listeners
                            UserThread.execute(lambda: result_handler(result))
                    case XmrTxProofRequestResult.SUCCESS:
                        logger.info(f"{result} succeeded")
                        UserThread.execute(lambda: result_handler(result))
                        self.terminate()
                    case XmrTxProofRequestResult.FAILED | XmrTxProofRequestResult.ERROR:
                        UserThread.execute(lambda: result_handler(result))
                        self.terminate()
                    case _:
                        logger.warning(f"Unexpected result {result}")
                
            except Exception as e:
                error_message = f"{self} failed with error {e}"
                fault_handler(error_message, e)
                UserThread.execute(lambda: result_handler(XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.CONNECTION_FAILURE.with_error(error_message))))
                
        future.add_done_callback(on_done)
        
        return future
        
    async def _get_result_from_raw_tx_request(self):
        # The rawtransaction endpoint is not documented in explorer docs.
        # Example request: https://xmrblocks.bisq.services/api/rawtransaction/5e665addf6d7c6300670e8a89564ed12b5c1a21c336408e2835668f9a6a0d802
        param = f"/api/rawtransaction/{self.model.tx_hash}"
        logger.info(f"Param {param} for rawtransaction request {self}")
        json = await self.http_client.get(param)
        try:
            pretty_json = JsonUtil.object_to_json(JsonUtil.parse_json(json))
            logger.info(f"Response json from rawtransaction request {self}\n{pretty_json}")
        except Exception as e:
            logger.error(f"Pretty print caused a {e}: raw json={json}")
        
        result = self.raw_tx_parser.parse(json)
        logger.info(f"Result from rawtransaction request {self}\n{result}")
        return result
    
    async def _get_result_from_tx_proof_request(self):
        # The API use the viewkey param for txKey if txprove is true
        # https://github.com/moneroexamples/onion-monero-blockchain-explorer/blob/9a37839f37abef0b8b94ceeba41ab51a41f3fbd8/src/page.h#L5254
        param = f"/api/outputs?txhash={self.model.tx_hash}&address={self.model.recipient_address}&viewkey={self.model.tx_key}&txprove=1"
        logger.info(f"Param {param} for {self}")
        json = await self.http_client.get(param)
        try:
            pretty_json = JsonUtil.object_to_json(JsonUtil.parse_json(json))
            logger.info(f"Response json from {self}\n{pretty_json}")
        except Exception as e:
            logger.error(f"Pretty print caused a {e}: raw json={json}")
        
        result = self.tx_proof_parser.parse(json, model=self.model)
        logger.info(f"Result from {self}\n{result}")
        return result

    def terminate(self):
        if self.request_future:
            self.request_future.cancel()
        self.terminated = True

    def __str__(self):
        return f"Request at: {self.model.service_address} for trade: {self.model.trade_id}"

    def _get_short_id(self):
        return f"{get_short_id(self.model.trade_id)} @ {self.model.service_address[:6]}"

    def _is_timeout_reached(self):
        return (get_time_ms() - self.first_request) > XmrTxProofRequest.MAX_REQUEST_PERIOD.total_seconds() * 1000
    
    def __hash__(self):
        return hash((self.model.trade_id, self.model.service_address, self.model.recipient_address, self.model.tx_hash, self.model.tx_key, self.model.amount, self.model.trade_date))

