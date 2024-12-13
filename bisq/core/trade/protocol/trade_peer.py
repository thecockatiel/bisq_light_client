
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload

@runtime_checkable
class _TradePeerProtocol(Protocol):
    pub_key_ring: "PubKeyRing"

class TradePeer(PersistablePayload, _TradePeerProtocol, ABC):
    pass