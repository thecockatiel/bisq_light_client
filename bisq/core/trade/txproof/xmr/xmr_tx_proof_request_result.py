from enum import EnumMeta, IntEnum

from bisq.core.trade.txproof.asset_tx_proof_request import AssetTxProofRequestResult
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_detail import XmrTxProofRequestDetail


class _CombinedMeta(EnumMeta, type(AssetTxProofRequestResult)):
    pass


# TODO: java sanity check

class XmrTxProofRequestResult(IntEnum, metaclass=_CombinedMeta):
    PENDING = 0
    """Tx not visible in network yet, unconfirmed or not enough confirmations"""
    
    SUCCESS = 1
    """Proof succeeded"""
    
    FAILED  = 2
    """Proof failed"""
    
    ERROR   = 3
    """Error from service, does not mean that proof failed"""
    
    def with_detail(self, detail: 'XmrTxProofRequestDetail') -> 'XmrTxProofRequestResult':
        setattr(self, 'detail', detail)
        return self
    
    def __str__(self):
        return f"XmrTxProofRequestResult{{\n     detail={getattr(self, 'detail', None)}\n}} "
