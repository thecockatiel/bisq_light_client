import unittest
from utils.wrappers import LazySequenceWrapper 


class TestLazySequenceWrapper(unittest.TestCase):
    def setUp(self):
        self.test_list = [1, 2, 3, 4, 5]
        self.lazy_seq = LazySequenceWrapper(lambda: self.test_list, lambda item, _: str(item))
    
    def test_length(self):
        self.assertEqual(len(self.lazy_seq), 5)
    
    def test_getitem(self):
        self.assertEqual(self.lazy_seq[0], "1")
        self.assertEqual(self.lazy_seq[-1], "5")
        self.assertEqual(self.lazy_seq[1:3], ["2", "3"])
    
    def test_iteration(self):
        result = []
        for item in self.lazy_seq:
            result.append(item)
        self.assertEqual(result, ["1", "2", "3", "4", "5"])
    
    def test_lazy_evaluation(self):
        
        called_times = 0
        def lazy_data():
            nonlocal called_times
            called_times += 1
            return [1, 2, 3]
        
        lazy_seq = LazySequenceWrapper(lazy_data, lambda item, _: str(item))
        self.assertEqual(called_times, 0)  # Not evaluated yet
        
        _ = len(lazy_seq)  # Force evaluation
        self.assertEqual(called_times, 1)  # Now evaluated
        
        _ = len(lazy_seq)  # Should use cached value
        self.assertEqual(called_times, 1)  # No additional evaluation
        
        self.assertEqual(lazy_seq[0], "1")
        self.assertEqual(lazy_seq._initialized_idx, {0: "1"})

if __name__ == '__main__':
    unittest.main()
