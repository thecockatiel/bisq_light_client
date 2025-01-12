from concurrent.futures import Future
import unittest
from math import inf, pow
import uuid
import random
import string
import asyncio
from bisq.common.crypto.hash_cash_service import HashCashService
from bisq.common.crypto.hash_cash_service_work import number_of_leading_zeros, to_num_leading_zeros
from bisq.common.crypto.proof_of_work import ProofOfWork
from bisq.common.setup.log_setup import get_logger
from utils.time import get_time_ms

logger = get_logger(__name__)

class TestHashCashService(unittest.TestCase):
    def test_number_of_leading_zeros(self):
        self.assertEqual(8, number_of_leading_zeros(bytes([0x0])))
        self.assertEqual(0, number_of_leading_zeros(bytes([0xFF])))
        self.assertEqual(6, number_of_leading_zeros(bytes([0x2])))
        self.assertEqual(2, number_of_leading_zeros(bytes([0x20])))  # 00100000 in binary
        self.assertEqual(1, number_of_leading_zeros(bytes([0x40, 0x00])))  # 01000000 00000000
        self.assertEqual(9, number_of_leading_zeros(bytes([0x00, 0x40])))  # 00000000 01000000
        self.assertEqual(17, number_of_leading_zeros(bytes([0x00, 0x00, 0x40])))  # 00000000 00000000 01000000
        self.assertEqual(9, number_of_leading_zeros(bytes([0x00, 0x50])))  # 00000000 01010000

    def test_to_num_leading_zeros(self):
        self.assertEqual(0, to_num_leading_zeros(-1.0))
        self.assertEqual(0, to_num_leading_zeros(0.0))
        self.assertEqual(0, to_num_leading_zeros(1.0))
        self.assertEqual(1, to_num_leading_zeros(1.1))
        self.assertEqual(1, to_num_leading_zeros(2.0))
        self.assertEqual(8, to_num_leading_zeros(256.0))
        self.assertEqual(1024, to_num_leading_zeros(inf))

    def do_runs(self, log2_difficulty: int, string_builder: list):
        difficulty = pow(2.0, log2_difficulty)
        num_tokens = 1000
        # Generate random string of 50 chars
        payload = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        ts = get_time_ms()
        tokens = list[Future[ProofOfWork]]()
        hash_service = HashCashService()
        
        for _ in range(num_tokens):
            challenge = str(uuid.uuid4()).encode('utf-8')
            pow_future = hash_service.mint(payload, challenge, difficulty)
            tokens.append(pow_future)
            
        size = len(tokens)
        tokens = ([token.result() for token in tokens]) # wait for all tokens to finish
        ts2 = get_time_ms()
        
        average_counter = sum(token.counter for token in tokens) / len(tokens)
        all_valid = all(HashCashService().verify(token) for token in tokens)
        
        self.assertTrue(all_valid)
        
        time1 = (get_time_ms() - ts) / size
        time2 = (get_time_ms() - ts2) / size
        
        string_builder.append(
            f"\nMinting {num_tokens} tokens with > {log2_difficulty} leading zeros "
            f"took {time1} ms per token and {average_counter:.0f} iterations in average. "
            f"Verification took {time2} ms per token."
        )

    def test_diff_increase(self):
        string_builder = []
        for i in range(9):
            self.do_runs(i, string_builder)
        logger.info(''.join(string_builder))

if __name__ == '__main__':
    unittest.main()