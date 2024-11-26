from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.common.crypto.proof_of_work import ProofOfWork


class ProofOfWorkPayload(ABC):
    @abstractmethod
    def get_proof_of_work() -> "ProofOfWork":
        pass
