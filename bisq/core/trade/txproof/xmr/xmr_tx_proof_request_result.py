from enum import Enum, EnumMeta
from typing import TYPE_CHECKING, Optional
from utils.hackyway import create_fake_copy_of_instance
from bisq.core.trade.txproof.asset_tx_proof_request import AssetTxProofRequestResult

if TYPE_CHECKING:
    from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_detail import XmrTxProofRequestDetail

class _CombinedMeta(EnumMeta, type(AssetTxProofRequestResult)):
    pass

class XmrTxProofRequestResult(Enum, metaclass=_CombinedMeta):
    PENDING = 0
    """Tx not visible in network yet, unconfirmed or not enough confirmations"""
    
    SUCCESS = 1
    """Proof succeeded"""
    
    FAILED  = 2
    """Proof failed"""
    
    ERROR   = 3
    """Error from service, does not mean that proof failed"""
    
    def __init__(self, *args):
        # numbers provided through args don't matter, values are assigned by __new__
        self.detail: Optional['XmrTxProofRequestDetail'] = None

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def with_detail(self, detail: 'XmrTxProofRequestDetail') -> 'XmrTxProofRequestResult':
        return create_fake_copy_of_instance(self, {"detail": detail})
    
    def __str__(self):
        return f"XmrTxProofRequestResult{{\n     detail={self.detail}\n}} "
