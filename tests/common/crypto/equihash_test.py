import math
import unittest
from bisq.common.crypto.equihash import Equihash, EquihashPuzzleSolution, count_all_solutions_for_nonce, deserialize_equihash_puzzle_solution, find_equihash_solution
from bisq.common.setup.log_setup import get_logger 
import time

logger = get_logger(__name__)

SAMPLE_NO = 10000

def hex_string(ints: list[int]):
    # Mask to 32 bits to match Java behavior
    return ' '.join(f'{(n & 0xFFFFFFFF):08x}' for n in ints)

def hub(difficulty):
    return hex_string(Equihash.get_hash_upper_bound(difficulty))

def expected_stats_from_poisson_distribution(mean: float) -> dict[int, int]:
    result = {}
    prob = math.exp(-mean)
    round_error = 0.0
    total = 0
    i = 0
    
    while total < SAMPLE_NO:
        n = int(round_error + prob * SAMPLE_NO + 0.5)
        if n > 0:
            result[i] = n
        round_error += prob * SAMPLE_NO - n
        total += n
        i += 1
        prob *= mean / (i)
    
    return result

class TestEquiHash(unittest.TestCase):
    
    def test_hash_upper_bound(self):
        self.assertEqual("ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff", hub(1))
        self.assertEqual("aaaaaaaa aaaaaaaa aaaaaaaa aaaaaaaa aaaaaaaa aaaaaaaa aaaaaaaa aaaaaaaa", hub(1.5))
        self.assertEqual("7fffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff", hub(2))
        self.assertEqual("55555555 55555555 55555555 55555555 55555555 55555555 55555555 55555555", hub(3))
        self.assertEqual("3fffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff", hub(4))
        self.assertEqual("33333333 33333333 33333333 33333333 33333333 33333333 33333333 33333333", hub(5))
        self.assertEqual("051eb851 eb851eb8 51eb851e b851eb85 1eb851eb 851eb851 eb851eb8 51eb851e", hub(50.0))
        self.assertEqual("0083126e 978d4fdf 3b645a1c ac083126 e978d4fd f3b645a1 cac08312 6e978d4f", hub(500.0))
        self.assertEqual("00000000 00000000 2f394219 248446ba a23d2ec7 29af3d61 0607aa01 67dd94ca", hub(1.0e20))
        self.assertEqual("00000000 00000000 00000000 00000000 ffffffff ffffffff ffffffff ffffffff", hub(3.402823669209385E38))
        self.assertEqual("00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000", hub(float('inf')))
        
    def test_adjust_difficulty(self):
        self.assertAlmostEqual(1.0, Equihash.adjust_difficulty(0.0), delta=0.0001)
        self.assertAlmostEqual(1.0, Equihash.adjust_difficulty(0.5), delta=0.0001)
        self.assertAlmostEqual(1.0, Equihash.adjust_difficulty(1.0), delta=0.0001)
        self.assertAlmostEqual(1.0, Equihash.adjust_difficulty(1.1), delta=0.0001)
        self.assertAlmostEqual(1.12, Equihash.adjust_difficulty(1.2), delta=0.01)
        self.assertAlmostEqual(1.83, Equihash.adjust_difficulty(1.5), delta=0.01)
        self.assertAlmostEqual(2.89, Equihash.adjust_difficulty(2.0), delta=0.01)
        self.assertAlmostEqual(3.92, Equihash.adjust_difficulty(2.5), delta=0.01)
        self.assertAlmostEqual(4.93, Equihash.adjust_difficulty(3.0), delta=0.01)
        self.assertAlmostEqual(200.0, Equihash.adjust_difficulty(100.0), delta=1.5)
        self.assertAlmostEqual(float('inf'), Equihash.adjust_difficulty(float('inf')), delta=1.0)
        
    def test_find_solution(self):
        equihash = Equihash(90, 5, 2.0)
        seed = bytes(32)
        solution = find_equihash_solution(equihash, seed)
        
        solution_bytes = solution.serialize()
        nonce, inputs = deserialize_equihash_puzzle_solution(solution_bytes, equihash)
        round_tripped_solution = EquihashPuzzleSolution(equihash, seed, nonce, inputs)
        
        self.assertTrue(solution.verify())
        self.assertEqual(72, len(solution_bytes))
        self.assertEqual(str(solution), str(round_tripped_solution))
        
    
    @unittest.skip("disabled")
    def test_benchmark_find_solution(self):
        adjusted_difficulty = Equihash.adjust_difficulty(2.0)
        equihash = Equihash(90, 5, adjusted_difficulty)
        total_count = 1000

        start_time = time.time()
        
        for i in range(total_count):
            seed = bytes([0] * 28 + [0, 0, 0, i])
            find_equihash_solution(equihash, seed)
        
        duration = time.time() - start_time
        
        logger.info(f"For Equihash-90-5 with real difficulty 2.0, adjusted difficulty {adjusted_difficulty} ...")
        logger.info(f"Total elapsed solution time: {int(duration * 1000)} ms")
        logger.info(f"Mean time to solve one puzzle: {int(duration * 1000 / total_count)} ms")
        logger.info(f"Puzzle solution time per unit difficulty: {int(duration * 1000 / (2 * total_count))} ms")
        
    @unittest.skip("disabled")
    def test_solution_count_per_nonce_stats(self):
        equihash = Equihash(90, 5, 1.0)
        seed = bytes(32)
        stats = {}

        for nonce in range(SAMPLE_NO):
            count = count_all_solutions_for_nonce(equihash, seed, nonce)
            stats[count] = stats.get(count, 0) + 1

        mean = sum(k * v for k, v in stats.items()) / SAMPLE_NO

        logger.info("For Equihash-90-5...")
        logger.info(f"Got puzzle solution count mean: {mean}")
        logger.info(f"Got expected count stats: {expected_stats_from_poisson_distribution(mean)}")
        logger.info(f"Got actual count stats: {stats}")

if __name__ == '__main__':
    unittest.main()