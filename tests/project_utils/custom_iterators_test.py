import unittest
from utils.custom_iterators import distinct_iterator, not_none_iterator

class CountingIterator:
    def __init__(self):
        self.count = 0
        self.values = [1, 2, 1, 2, 3]
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.values):
            raise StopIteration
        self.count += 1
        value = self.values[self.index]
        self.index += 1
        return value

class TestUniqueIterator(unittest.TestCase):
    def test_distinct_iterator(self):
        data = [1, 2, 2, 3, 4, 4, 5]
        expected = [1, 2, 3, 4, 5]
        result = list(distinct_iterator(iter(data)))
        self.assertEqual(result, expected)
        
    def test_not_none_iterator(self):
        data = [1, None, None, 2, None, 4, None, 5]
        expected = [1, 2, 4, 5]
        result = list(not_none_iterator(iter(data)))
        self.assertEqual(result, expected)

    def test_distinct_iterator_is_lazy(self):
        counter = CountingIterator()
        unique_iter = distinct_iterator(counter)
        
        # No items should be consumed yet
        self.assertEqual(counter.count, 0)
        
        # Take first item
        first = next(unique_iter)
        self.assertEqual(first, 1)
        self.assertEqual(counter.count, 1)
        
        # Take second item
        second = next(unique_iter)
        self.assertEqual(second, 2)
        self.assertEqual(counter.count, 2)
        
        # Take third item (should skip duplicate 1 and 2)
        third = next(unique_iter)
        self.assertEqual(third, 3)
        self.assertEqual(counter.count, 5)

    def test_not_none_iterator_is_lazy(self):
        counter = CountingIterator()
        filtered = not_none_iterator(counter)
        
        # No items should be consumed yet
        self.assertEqual(counter.count, 0)

        # Take first item
        first = next(filtered)
        self.assertEqual(first, 1)
        self.assertEqual(counter.count, 1)
        
        # Take second item (should skip duplicate 1)
        second = next(filtered)
        self.assertEqual(second, 2)
        self.assertEqual(counter.count, 2)

if __name__ == "__main__":
    unittest.main()
