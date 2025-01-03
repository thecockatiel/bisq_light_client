

from bisq.core.network.http.http_client_impl import HttpClientImpl
from bisq.core.trade.txproof.asset_tx_proof_httpclient import AssetTxProofHttpClient


class XmrTxProofHttpClient(HttpClientImpl, AssetTxProofHttpClient):
    pass
