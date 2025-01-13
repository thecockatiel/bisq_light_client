from concurrent.futures import Future
from multiprocessing import freeze_support 
from typing import Optional
from bisq.common.crypto.equihash import (
    Equihash,
    EquihashPuzzleSolution,
    deserialize_equihash_puzzle_solution,
    find_equihash_solution,
)
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.proof_of_work_service import ProofOfWorkService
from bisq.common.crypto.proof_of_work import ProofOfWork
from bisq.common.setup.log_setup import get_logger

from utils.time import get_time_ms
from concurrent.futures import ProcessPoolExecutor

logger = get_logger(__name__)


class EquihashProofOfWorkService(ProofOfWorkService):
    DIFFICULTY_SCALE_FACTOR = 3.0e-5
    """Rough cost of two Hashcash iterations compared to solving an Equihash-90-5 puzzle of unit difficulty."""

    def __init__(self, version: int):
        super().__init__(version)
        self._process_pool_executor: Optional[ProcessPoolExecutor] = None

    def mint(
        self, payload: bytes, challenge: bytes, difficulty: float
    ) -> Future[ProofOfWork]:
        if (
            self._process_pool_executor is None
            or self._process_pool_executor._shutdown_thread
        ):
            self._process_pool_executor = ProcessPoolExecutor(1)
        scaled_difficulty = EquihashProofOfWorkService._scaled_difficulty(difficulty)
        logger.info(f"Got scaled & adjusted difficulty: {scaled_difficulty}")

        future = Future[ProofOfWork]()
        ts = get_time_ms()
        executor_result = self._process_pool_executor.submit(
            find_equihash_solution,
            Equihash(90, 5, scaled_difficulty),
            self._get_seed(payload, challenge),
        )

        def on_done(f: Future["EquihashPuzzleSolution"]):
            try:
                solution = f.result().serialize()
                counter = int.from_bytes(solution[:8], byteorder="big")
                proof_of_work = ProofOfWork(
                    payload,
                    counter,
                    challenge,
                    difficulty,
                    get_time_ms() - ts,
                    solution,
                    self.version,
                )
                logger.info(f"Completed minting proofOfWork: {proof_of_work}")
                future.set_result(proof_of_work)
            except Exception as e:
                future.set_exception(e)

        executor_result.add_done_callback(on_done)
        return future

    def _get_seed(self, payload: bytes, challenge: bytes):
        return get_sha256_hash(payload + challenge)

    def get_challenge(self, item_id: str, owner_id: str):
        # Convert ids to strings with double spaces and concatenate with comma separator
        escaped_item_id = str(item_id).replace(" ", "  ")
        escaped_owner_id = str(owner_id).replace(" ", "  ")
        # Return SHA256 hash of the concatenated string
        return get_sha256_hash(
            (escaped_item_id + ", " + escaped_owner_id).encode("utf-8")
        )

    def verify(self, proof_of_work: ProofOfWork):
        scaled_difficulty = EquihashProofOfWorkService._scaled_difficulty(proof_of_work.difficulty)
        seed = self._get_seed(proof_of_work.payload, proof_of_work.challenge)
        equihash = Equihash(90, 5, scaled_difficulty)
        nonce, inputs = deserialize_equihash_puzzle_solution(
            proof_of_work.solution, equihash
        )
        solution = EquihashPuzzleSolution(equihash, seed, nonce, inputs)
        return solution.verify()

    @staticmethod
    def _scaled_difficulty(difficulty: float) -> float:
        return Equihash.adjust_difficulty(
            EquihashProofOfWorkService.DIFFICULTY_SCALE_FACTOR * difficulty
        )
        
    def shutdown(self):
        if self._process_pool_executor is not None:
            self._process_pool_executor.shutdown(wait=False, cancel_futures=True)
            self._process_pool_executor = None
