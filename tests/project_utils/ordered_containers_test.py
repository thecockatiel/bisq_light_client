import unittest
from utils.ordered_containers import OrderedSet

class TestOrderedSet(unittest.TestCase):
    def test_init(self):
        s = OrderedSet([1, 2, 3])
        self.assertEqual(list(s), [1, 2, 3])
        
    def test_add(self):
        s = OrderedSet()
        s.add(1)
        s.add(2)
        self.assertEqual(list(s), [1, 2])
        
    def test_remove(self):
        s = OrderedSet([1, 2, 3])
        s.remove(2)
        self.assertEqual(list(s), [1, 3])
        with self.assertRaises(KeyError):
            s.remove(4)
            
    def test_discard(self):
        s = OrderedSet([1, 2, 3])
        s.discard(2)
        s.discard(4)  # Should not raise
        self.assertEqual(list(s), [1, 3])
        
    def test_update(self):
        s = OrderedSet([1, 2])
        s.update([3, 4])
        self.assertEqual(list(s), [1, 2, 3, 4])
        
    def test_set_operations(self):
        s1 = OrderedSet([1, 2, 3])
        s2 = OrderedSet([2, 3, 4])
        
        self.assertEqual(list(s1.union(s2)), [1, 2, 3, 4])
        self.assertEqual(list(s1.intersection(s2)), [2, 3])
        self.assertEqual(list(s1.difference(s2)), [1])
        
    def test_contains(self):
        s = OrderedSet([1, 2, 3])
        self.assertTrue(2 in s)
        self.assertFalse(4 in s)
        
    def test_copy(self):
        s1 = OrderedSet([1, 2, 3])
        s2 = s1.copy()
        self.assertEqual(s1, s2)
        self.assertIsNot(s1, s2)
    
    def test_symmetric_difference(self):
        s1 = OrderedSet([1, 2, 3])
        s2 = OrderedSet([2, 3, 4])
        self.assertEqual(list(s1 ^ s2), [1, 4])
        
    def test_subset_superset(self):
        s1 = OrderedSet([1, 2])
        s2 = OrderedSet([1, 2, 3])
        self.assertTrue(s1.issubset(s2))
        self.assertTrue(s2.issuperset(s1))
        self.assertFalse(s2.issubset(s1))
        
    def test_update_operations(self):
        s1 = OrderedSet([1, 2, 3])
        s2 = OrderedSet([2, 3, 4])
        
        s3 = s1.copy()
        s3 &= s2
        self.assertEqual(list(s3), [2, 3])
        
        s3 = s1.copy()
        s3 -= s2
        self.assertEqual(list(s3), [1])
        
        s3 = s1.copy()
        s3 ^= s2
        self.assertEqual(list(s3), [1, 4])
        
    def test_operator_overloads(self):
        s1 = OrderedSet([1, 2, 3])
        s2 = OrderedSet([2, 3, 4])
        
        self.assertEqual(list(s1 | s2), [1, 2, 3, 4])
        self.assertEqual(list(s1 & s2), [2, 3])
        self.assertEqual(list(s1 - s2), [1])
        self.assertEqual(list(s1 ^ s2), [1, 4])

    def test_empty_set(self):
        s = OrderedSet()
        self.assertEqual(len(s), 0)
        self.assertEqual(list(s), [])

    def test_clear(self):
        s = OrderedSet([1, 2, 3])
        s.clear()
        self.assertEqual(len(s), 0)
        self.assertEqual(list(s), [])

    def test_pop(self):
        s = OrderedSet([1, 2, 3])
        self.assertEqual(s.pop(), 3)
        self.assertEqual(list(s), [1, 2])
        with self.assertRaises(KeyError):
            OrderedSet().pop()

    def test_len(self):
        s = OrderedSet([1, 2, 3])
        self.assertEqual(len(s), 3)
        s.add(4)
        self.assertEqual(len(s), 4)
        s.remove(1)
        self.assertEqual(len(s), 3)

    def test_iteration_order(self):
        items = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        s = OrderedSet(items)
        self.assertEqual(list(s), [3, 1, 4, 5, 9, 2, 6])

    def test_update_duplicates(self):
        s = OrderedSet([1, 2, 3])
        s.update([2, 3, 4, 3, 2])
        self.assertEqual(list(s), [1, 2, 3, 4])

    def test_repr(self):
        s = OrderedSet([1, 2, 3])
        self.assertEqual(repr(s), "OrderedSet([1, 2, 3])")

if __name__ == '__main__':
    unittest.main()
