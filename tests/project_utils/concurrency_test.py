import unittest
import weakref
from utils.concurrency import ThreadSafeDict, ThreadSafeSet, ThreadSafeWeakSet, ThreadSafeList, AtomicBoolean, AtomicInt
import threading
import time

class TestThreadSafeSet(unittest.TestCase):
    def setUp(self):
        self.safe_set = ThreadSafeSet()
        
    def test_init_with_set(self):
        items = {1, 2, 3}
        safe_set = ThreadSafeSet(items)
        self.assertEqual(safe_set._set, items)

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

    def test_clear(self):
        for i in range(5):
            self.safe_set.add(i)
        self.safe_set.clear()
        self.assertEqual(len(self.safe_set), 0)

    def test_iteration(self):
        items = {1, 2, 3, 4, 5}
        for item in items:
            self.safe_set.add(item)
        self.assertEqual(set(iter(self.safe_set)), items)

    def test_concurrent_iteration(self):
        # Test that iteration is safe while modifications occur
        def modifier():
            for i in range(100):
                self.safe_set.add(i)
                if i % 2 == 0:
                    self.safe_set.discard(i)
                time.sleep(0.001)

        def iterator():
            for _ in range(50):
                # This should not raise any exceptions
                list(iter(self.safe_set))
                time.sleep(0.001)

        threads = [
            threading.Thread(target=modifier),
            threading.Thread(target=iterator)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

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

    def test_cleanup(self):
        class TestObj:
            pass
        
        obj1, obj2 = TestObj(), TestObj()
        self.weak_set.add(obj1)
        self.weak_set.add(obj2)
        
        del obj1
        self.weak_set.cleanup()
        self.assertEqual(len(list(iter(self.weak_set))), 1)

    def test_remove_and_discard(self):
        class TestObj:
            pass
        
        obj = TestObj()
        self.weak_set.add(obj)
        self.weak_set.remove(obj)
        self.assertEqual(len(list(iter(self.weak_set))), 0)
        
        # Should not raise exception
        self.weak_set.discard(obj)

    def test_concurrent_cleanup(self):
        class TestObj:
            pass

        live_objects = []
        for _ in range(100):
            obj = TestObj()
            live_objects.append(obj)
            self.weak_set.add(obj)

        def cleanup_thread():
            for _ in range(10):
                self.weak_set.cleanup()
                time.sleep(0.001)

        def iterator_thread():
            for _ in range(10):
                list(iter(self.weak_set))
                time.sleep(0.001)

        threads = [
            threading.Thread(target=cleanup_thread),
            threading.Thread(target=iterator_thread)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(list(iter(self.weak_set))), 100)

class TestConcurrentDict(unittest.TestCase):
    def setUp(self):
        self.concurrent_dict = ThreadSafeDict()

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

    def test_update(self):
        other_dict = {'key1': 'value1', 'key2': 'value2'}
        self.concurrent_dict.update(other_dict)
        self.assertEqual(self.concurrent_dict.get('key1'), 'value1')
        self.assertEqual(self.concurrent_dict.get('key2'), 'value2')

    def test_items_and_values(self):
        test_dict = {'key1': 'value1', 'key2': 'value2'}
        self.concurrent_dict.update(test_dict)
        
        self.assertEqual(dict(self.concurrent_dict.items()), test_dict)
        self.assertEqual(set(self.concurrent_dict.values()), set(test_dict.values()))

    def test_with_items(self):
        test_dict = {'key1': 'value1', 'key2': 'value2'}
        self.concurrent_dict.update(test_dict)
        
        result = self.concurrent_dict.with_items(lambda items: {k: v for k, v in items})
        self.assertEqual(result, test_dict)

    def test_get_and_put(self):
        def increment_value(value):
            return value + 1

        threads = []
        for _ in range(10):
            t = threading.Thread(
                target=lambda: self.concurrent_dict.get_and_put('counter', increment_value, 0)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(self.concurrent_dict.get('counter'), 10)

    def test_dict_operations(self):
        # Test dict-like operations
        self.concurrent_dict['key'] = 'value'
        self.assertEqual(self.concurrent_dict['key'], 'value')
        
        del self.concurrent_dict['key']
        self.assertFalse('key' in self.concurrent_dict)
        
        with self.assertRaises(KeyError):
            _ = self.concurrent_dict['nonexistent']

class TestConcurrentList(unittest.TestCase):
    def setUp(self):
        self.concurrent_list = ThreadSafeList()

    def test_append_and_extend(self):
        self.concurrent_list.append(1)
        self.concurrent_list.extend([2, 3])
        self.assertEqual(list(self.concurrent_list), [1, 2, 3])

    def test_pop_and_remove(self):
        self.concurrent_list.extend([1, 2, 3])
        self.assertEqual(self.concurrent_list.pop(), 3)
        self.concurrent_list.remove(1)
        self.assertEqual(list(self.concurrent_list), [2])

    def test_insert_and_clear(self):
        self.concurrent_list.extend([1, 3])
        self.concurrent_list.insert(1, 2)
        self.assertEqual(list(self.concurrent_list), [1, 2, 3])
        self.concurrent_list.clear()
        self.assertEqual(len(self.concurrent_list), 0)

    def test_getitem_setitem(self):
        self.concurrent_list.extend([1, 2, 3])
        self.assertEqual(self.concurrent_list[1], 2)
        self.concurrent_list[1] = 4
        self.assertEqual(self.concurrent_list[1], 4)

    def test_thread_safety_list(self):
        def add_items():
            for i in range(100):
                self.concurrent_list.append(i)
                time.sleep(0.001)

        threads = [threading.Thread(target=add_items) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.concurrent_list), 300)

    def test_concurrent_iteration(self):
        # Fill list with initial values
        self.concurrent_list.extend(range(100))

        def modifier():
            for i in range(50):
                self.concurrent_list.append(i)
                if len(self.concurrent_list) > 0:
                    self.concurrent_list.pop(0)
                time.sleep(0.001)

        def iterator():
            for _ in range(50):
                # Should not raise any exceptions
                for item in self.concurrent_list:
                    _ = item
                time.sleep(0.001)

        threads = [
            threading.Thread(target=modifier),
            threading.Thread(target=iterator)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

class TestAtomicBoolean(unittest.TestCase):
    def setUp(self):
        self.atomic_bool = AtomicBoolean()

    def test_get_and_set(self):
        self.assertFalse(self.atomic_bool.get())
        self.atomic_bool.set(True)
        self.assertTrue(self.atomic_bool.get())

    def test_get_and_set_atomic(self):
        old_value = self.atomic_bool.get_and_set(True)
        self.assertFalse(old_value)
        self.assertTrue(self.atomic_bool.get())

    def test_compare_and_set(self):
        self.assertTrue(self.atomic_bool.compare_and_set(False, True))
        self.assertFalse(self.atomic_bool.compare_and_set(False, True))

    def test_bool_conversion(self):
        self.assertFalse(bool(self.atomic_bool))
        self.atomic_bool.set(True)
        self.assertTrue(bool(self.atomic_bool))

class TestAtomicInt(unittest.TestCase):
    def setUp(self):
        self.atomic_int = AtomicInt()

    def test_get_and_set(self):
        self.assertEqual(self.atomic_int.get(), 0)
        self.atomic_int.set(5)
        self.assertEqual(self.atomic_int.get(), 5)

    def test_get_and_set_atomic(self):
        old_value = self.atomic_int.get_and_set(10)
        self.assertEqual(old_value, 0)
        self.assertEqual(self.atomic_int.get(), 10)

    def test_compare_and_set(self):
        self.assertTrue(self.atomic_int.compare_and_set(0, 5))
        self.assertFalse(self.atomic_int.compare_and_set(0, 10))

    def test_add_and_get(self):
        self.assertEqual(self.atomic_int.add_and_get(5), 5)
        self.assertEqual(self.atomic_int.add_and_get(-2), 3)

    def test_get_and_add(self):
        self.assertEqual(self.atomic_int.get_and_add(5), 0)
        self.assertEqual(self.atomic_int.get_and_add(-2), 5)

    def test_increment_decrement(self):
        self.assertEqual(self.atomic_int.increment_and_get(), 1)
        self.assertEqual(self.atomic_int.get_and_increment(), 1)
        self.assertEqual(self.atomic_int.decrement_and_get(), 1)
        self.assertEqual(self.atomic_int.get_and_decrement(), 1)

class TestDeadlocks(unittest.TestCase):
    def setUp(self):
        self.safe_set = ThreadSafeSet()
        self.weak_set = ThreadSafeWeakSet()
        self.concurrent_dict = ThreadSafeDict()
        self.concurrent_list = ThreadSafeList()
        self.event = threading.Event()
        self.timeout = 2  # seconds

    def test_threadsafe_set_deadlock(self):
        def concurrent_operations():
            for _ in range(100):
                self.safe_set.add(1)
                _ = iter(self.safe_set)  # Read operation
                self.safe_set.remove(1)
            self.event.set()

        threads = [threading.Thread(target=concurrent_operations) for _ in range(10)]
        for t in threads:
            t.start()
        
        # If there's a deadlock, event.wait() will timeout
        self.assertTrue(self.event.wait(self.timeout))
        for t in threads:
            t.join(self.timeout)
            self.assertFalse(t.is_alive())

    def test_threadsafe_weakset_deadlock(self):
        class TestObj:
            pass

        def concurrent_operations():
            for _ in range(100):
                obj = TestObj()
                self.weak_set.add(obj)
                _ = list(iter(self.weak_set))  # Force iteration
                self.weak_set.cleanup()  # Trigger cleanup while iterating
            self.event.set()

        threads = [threading.Thread(target=concurrent_operations) for _ in range(10)]
        for t in threads:
            t.start()
        
        self.assertTrue(self.event.wait(self.timeout))
        for t in threads:
            t.join(self.timeout)
            self.assertFalse(t.is_alive())

    def test_concurrent_dict_deadlock(self):
        def concurrent_operations():
            for i in range(100):
                self.concurrent_dict.put(f'key{i}', i)
                _ = self.concurrent_dict.items()  # Read operation
                self.concurrent_dict.remove(f'key{i}')
                # Test nested lock acquisition
                self.concurrent_dict.with_items(lambda items: len(list(items)))
            self.event.set()

        threads = [threading.Thread(target=concurrent_operations) for _ in range(10)]
        for t in threads:
            t.start()
        
        self.assertTrue(self.event.wait(self.timeout))
        for t in threads:
            t.join(self.timeout)
            self.assertFalse(t.is_alive())

    def test_concurrent_list_deadlock(self):
        def concurrent_operations():
            for i in range(100):
                self.concurrent_list.append(i)
                _ = iter(self.concurrent_list)  # Read operation
                if len(self.concurrent_list) > 0:
                    self.concurrent_list.pop()
                # Mix read/write operations
                if i in self.concurrent_list:
                    self.concurrent_list.remove(i)
            self.event.set()

        threads = [threading.Thread(target=concurrent_operations) for _ in range(10)]
        for t in threads:
            t.start()
        
        self.assertTrue(self.event.wait(self.timeout))
        for t in threads:
            t.join(self.timeout)
            self.assertFalse(t.is_alive())

if __name__ == '__main__':
    unittest.main()