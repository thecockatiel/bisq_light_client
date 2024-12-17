from typing import TYPE_CHECKING
from bitcoinj.core.transaction_confidence import TransactionConfidence

if TYPE_CHECKING: 
    from bitcoinj.core.address import Address


class AddressConfidenceListener:

    def __init__(self, address: "Address"):
        self.address = address

    def on_transaction_confidence_changed(self, confidence: "TransactionConfidence"):
        pass
