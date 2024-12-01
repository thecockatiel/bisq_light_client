
from abc import ABC, abstractmethod
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload


class TradePeer(PersistablePayload, ABC):
    @abstractmethod
    def get_pub_key_ring(self) -> "PubKeyRing":
        pass
    
    @abstractmethod
    def set_pub_key_ring(self, pub_key_ring: "PubKeyRing") -> None:
        pass