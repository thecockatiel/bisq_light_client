import unittest
import weakref
from utils.concurrency import ConcurrentDict, ThreadSafeSet, ThreadSafeWeakSet
import threading
import time

class TestThreadSafeSet(unittest.TestCase):
    def setUp(self):
        self.safe_set = ThreadSafeSet()

    def test_add_and_contains(self):
        self.safe_set.add(1)
        self.assertTrue(1 in self.safe_set)
        self.assertFalse(2 in self.safe_set)

    def test_remove(self):
        self.safe_set.add(1)
        self.safe_set.remove(1)
        self.assertFalse(1 in self.safe_set)
        with self.assertRaises(KeyError):
            self.safe_set.remove(2)

    def test_discard(self):
        self.safe_set.add(1)
        self.safe_set.discard(1)
        self.assertFalse(1 in self.safe_set)
        # Should not raise exception
        self.safe_set.discard(2)

    def test_thread_safety(self):
        def add_items():
            for i in range(100):
                self.safe_set.add(i)
                time.sleep(0.001)

        threads = [threading.Thread(target=add_items) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.safe_set), 100)

class TestThreadSafeWeakSet(unittest.TestCase):
    def setUp(self):
        self.weak_set = ThreadSafeWeakSet()

    def test_weak_references(self):
        class TestObj:
            pass

        obj = TestObj()
        self.weak_set.add(obj)
        self.assertTrue(obj in iter(self.weak_set))
        
        # When object is deleted, it should be removed from set
        del obj
        self.assertEqual(len(list(iter(self.weak_set))), 0)

    def test_thread_safety_weak(self):
        class TestObj:
            pass

        def add_items():
            for _ in range(100):
                obj = TestObj()
                self.weak_set.add(obj)
                time.sleep(0.001)

        threads = [threading.Thread(target=add_items) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Objects should be garbage collected since no references remain
        self.assertEqual(len(list(iter(self.weak_set))), 0)

class TestConcurrentDict(unittest.TestCase):
    def setUp(self):
        self.concurrent_dict = ConcurrentDict()

    def test_put_and_get(self):
        self.concurrent_dict.put('key1', 'value1')
        self.assertEqual(self.concurrent_dict.get('key1'), 'value1')
        self.assertIsNone(self.concurrent_dict.get('key2'))

    def test_remove(self):
        self.concurrent_dict.put('key1', 'value1')
        self.assertEqual(self.concurrent_dict.remove('key1'), 'value1')
        self.assertIsNone(self.concurrent_dict.get('key1'))
        self.assertIsNone(self.concurrent_dict.remove('key2'))

    def test_thread_safety(self):
        def put_items():
            for i in range(100):
                self.concurrent_dict.put(f'key{i}', f'value{i}')
                time.sleep(0.001)

        threads = [threading.Thread(target=put_items) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.concurrent_dict._dict), 100)
        for i in range(100):
            self.assertEqual(self.concurrent_dict.get(f'key{i}'), f'value{i}')

if __name__ == '__main__':
    unittest.main()