from bisq.core.network.http.async_http_client_impl import AsyncHttpClientImpl
from bisq.core.trade.txproof.asset_tx_proof_httpclient import AssetTxProofHttpClient


class TxBroadcastHttpClient(AsyncHttpClientImpl, AssetTxProofHttpClient):
    pass
