from abc import ABC

from bisq.core.support.dispute.messages.dispute_message import DisputeMessage

class ArbitrationMessage(DisputeMessage, ABC):
    pass