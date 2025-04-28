from typing import Optional
from bisq.common.crypto.hash_cash_service_work import (
    do_mint,
    number_of_leading_zeros,
    to_num_leading_zeros,
    to_sha256_hash,
)
from bisq.common.crypto.proof_of_work_service import ProofOfWorkService
from bisq.common.crypto.proof_of_work import ProofOfWork

from bisq.common.setup.log_setup import get_ctx_logger
from utils.aio import FutureCallback
from utils.time import get_time_ms
from concurrent.futures import ProcessPoolExecutor, Future


class HashCashService(ProofOfWorkService):
    def __init__(self):
        super().__init__(0)
        self._process_pool_executor: Optional[ProcessPoolExecutor] = None
        self.logger = get_ctx_logger(__name__)

    def mint(
        self, payload: bytes, challenge: bytes, difficulty: float
    ) -> Future[ProofOfWork]:
        if (
            self._process_pool_executor is None
            or self._process_pool_executor._shutdown_thread
        ):
            self._process_pool_executor = ProcessPoolExecutor(1)

        future = Future[ProofOfWork]()
        ts = get_time_ms()
        executor_result = self._process_pool_executor.submit(
            do_mint,
            payload,
            challenge,
            difficulty,
        )

        def on_success(result: tuple[int, bytes]):
            counter, solution = result
            proof_of_work = ProofOfWork(
                payload,
                counter,
                challenge,
                difficulty,
                get_time_ms() - ts,
                solution,
                0,
            )
            self.logger.info(f"Completed minting proofOfWork: {proof_of_work}")
            future.set_result(proof_of_work)

        def on_failure(e):
            future.set_exception(e)

        executor_result.add_done_callback(FutureCallback(on_success, on_failure))
        return future

    def verify(self, proof_of_work: ProofOfWork) -> bool:
        hash_result = to_sha256_hash(
            proof_of_work.payload,
            proof_of_work.challenge,
            proof_of_work.counter,
        )
        return number_of_leading_zeros(hash_result) > to_num_leading_zeros(
            proof_of_work.difficulty
        )

    def get_challenge(self, item_id: str, owner_id: str) -> bytes:
        return HashCashService.get_bytes(item_id + owner_id)

    def shut_down(self):
        if self._process_pool_executor is not None:
            self._process_pool_executor.shutdown(wait=False, cancel_futures=True)
            self._process_pool_executor = None

    @staticmethod
    def get_bytes(value: str) -> bytes:
        return value.encode("utf-8")
