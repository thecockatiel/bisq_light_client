import asyncio
from concurrent.futures import Future
from multiprocessing import freeze_support
import sys
from typing import Optional
from bisq.common.crypto.hash_cash_service_work import (
    do_mint,
    number_of_leading_zeros,
    to_num_leading_zeros,
    to_sha256_hash,
)
from bisq.common.crypto.proof_of_work_service import ProofOfWorkService
from bisq.common.crypto.proof_of_work import ProofOfWork
from bisq.common.setup.log_setup import get_logger

from utils.time import get_time_ms
from concurrent.futures import ProcessPoolExecutor

logger = get_logger(__name__)

class HashCashService(ProofOfWorkService):
    def __init__(self):
        super().__init__(0)
        self._process_pool_executor: Optional[ProcessPoolExecutor] = None

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

        def on_done(f: Future[tuple[int, bytes]]):
            try:
                counter, solution = f.result()
                proof_of_work = ProofOfWork(
                    payload,
                    counter,
                    challenge,
                    difficulty,
                    get_time_ms() - ts,
                    solution,
                    0,
                )
                logger.info(f"Completed minting proofOfWork: {proof_of_work}")
                future.set_result(proof_of_work)
            except Exception as e:
                future.set_exception(e)

        executor_result.add_done_callback(on_done)
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

    def shutdown(self):
        if self._process_pool_executor is not None:
            self._process_pool_executor.shutdown(wait=False, cancel_futures=True)
            self._process_pool_executor = None

    @staticmethod
    def get_bytes(value: str) -> bytes:
        return value.encode("utf-8")
