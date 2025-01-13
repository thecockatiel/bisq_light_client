from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.common.crypto.proof_of_work import ProofOfWork

class ProofOfWorkService(ABC):
    def __init__(self, version: int):
        self._version = version

    @property
    def version(self) -> int:
        return self._version

    @abstractmethod
    def mint(
        self, payload: bytes, challenge: bytes, difficulty: float
    ) -> Future["ProofOfWork"]:
        pass

    @abstractmethod
    def verify(self, proof_of_work: "ProofOfWork") -> bool:
        pass

    def get_payload(self, item_id: str) -> bytes:
        return item_id.encode("utf-8")

    @abstractmethod
    def get_challenge(self, item_id: str, owner_id: str) -> bytes:
        pass

    def mint_with_ids(self, item_id: str, owner_id: str, difficulty: float) -> Future:
        return self.mint(
            self.get_payload(item_id),
            self.get_challenge(item_id, owner_id),
            difficulty,
        )

    def verify_with_ids(
        self,
        proof_of_work: "ProofOfWork",
        item_id: str,
        owner_id: str,
        control_difficulty: float,
    ) -> bool:
        if proof_of_work.version != self.version:
            raise ValueError("Version mismatch")

        control_challenge = self.get_challenge(item_id, owner_id)
        return (
            proof_of_work.challenge == control_challenge
            and proof_of_work.difficulty >= control_difficulty
            and self.verify(proof_of_work)
        )
