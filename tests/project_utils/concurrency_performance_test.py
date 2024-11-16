import unittest
from utils.concurrency import ThreadSafeDict, ThreadSafeSet, ThreadSafeWeakSet, ThreadSafeList, AtomicBoolean, AtomicInt
import threading
import time
import os

if 'TERM_PROGRAM' in os.environ.keys() and os.environ['TERM_PROGRAM'] == 'vscode':
    running_in_vscode = True
else:
    running_in_vscode = False

@unittest.skipIf(not running_in_vscode, "No need to run the code in general")
class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.iterations = 10000
        self.thread_count = 4
        # Thread-safe collections
        self.safe_set = ThreadSafeSet()
        self.weak_set = ThreadSafeWeakSet()
        self.safe_dict = ThreadSafeDict()
        self.safe_list = ThreadSafeList()
        self.atomic_int = AtomicInt()
        # Normal collections
        self.normal_set = set()
        self.normal_dict = {}
        self.normal_list = []
        self.normal_int = 0
        # Lock for normal collections
        self.normal_lock = threading.Lock()

    def measure_time(self, func):
        start_time = time.time()
        func()
        return time.time() - start_time

    def test_set_performance(self):
        def safe_worker():
            for i in range(self.iterations):
                self.safe_set.add(i)
                _ = i in self.safe_set
                self.safe_set.remove(i)

        def normal_worker():
            for i in range(self.iterations):
                with self.normal_lock:
                    self.normal_set.add(i)
                    _ = i in self.normal_set
                    self.normal_set.remove(i)

        # Test ThreadSafeSet
        threads = [threading.Thread(target=safe_worker) for _ in range(self.thread_count)]
        safe_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        # Test normal set with lock
        threads = [threading.Thread(target=normal_worker) for _ in range(self.thread_count)]
        normal_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        operations = self.iterations * self.thread_count * 3
        print(f"\nSet Performance Comparison:")
        print(f"ThreadSafeSet: {operations/safe_duration:,.0f} ops/sec")
        print(f"Normal Set with Lock: {operations/normal_duration:,.0f} ops/sec")
        print(f"Relative Performance: {normal_duration/safe_duration:.2f}x")

    def test_dict_performance(self):
        def safe_worker():
            for i in range(self.iterations):
                self.safe_dict[i] = i
                _ = self.safe_dict.get(i)
                del self.safe_dict[i]

        def normal_worker():
            for i in range(self.iterations):
                with self.normal_lock:
                    self.normal_dict[i] = i
                    _ = self.normal_dict.get(i)
                    del self.normal_dict[i]

        # Test ThreadSafeDict
        threads = [threading.Thread(target=safe_worker) for _ in range(self.thread_count)]
        safe_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        # Test normal dict with lock
        threads = [threading.Thread(target=normal_worker) for _ in range(self.thread_count)]
        normal_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        operations = self.iterations * self.thread_count * 3
        print(f"\nDict Performance Comparison:")
        print(f"ThreadSafeDict: {operations/safe_duration:,.0f} ops/sec")
        print(f"Normal Dict with Lock: {operations/normal_duration:,.0f} ops/sec")
        print(f"Relative Performance: {normal_duration/safe_duration:.2f}x")

    def test_list_performance(self):
        def safe_worker():
            for i in range(self.iterations):
                self.safe_list.append(i)
                _ = i in self.safe_list
                if len(self.safe_list) > 0:
                    try:
                        self.safe_list.remove(i)
                    except ValueError:
                        pass

        def normal_worker():
            for i in range(self.iterations):
                with self.normal_lock:
                    self.normal_list.append(i)
                    _ = i in self.normal_list
                    if len(self.normal_list) > 0:
                        try:
                            self.normal_list.remove(i)
                        except ValueError:
                            pass

        # Test ThreadSafeList
        threads = [threading.Thread(target=safe_worker) for _ in range(self.thread_count)]
        safe_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        # Test normal list with lock
        threads = [threading.Thread(target=normal_worker) for _ in range(self.thread_count)]
        normal_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        operations = self.iterations * self.thread_count * 3
        print(f"\nList Performance Comparison:")
        print(f"ThreadSafeList: {operations/safe_duration:,.0f} ops/sec")
        print(f"Normal List with Lock: {operations/normal_duration:,.0f} ops/sec")
        print(f"Relative Performance: {normal_duration/safe_duration:.2f}x")

    def test_atomic_int_performance(self):
        def safe_worker():
            for _ in range(self.iterations):
                self.atomic_int.increment_and_get()
                self.atomic_int.get()
                self.atomic_int.decrement_and_get()

        def normal_worker():
            for _ in range(self.iterations):
                with self.normal_lock:
                    self.normal_int += 1
                    _ = self.normal_int
                    self.normal_int -= 1

        # Test AtomicInt
        threads = [threading.Thread(target=safe_worker) for _ in range(self.thread_count)]
        safe_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        # Test normal int with lock
        threads = [threading.Thread(target=normal_worker) for _ in range(self.thread_count)]
        normal_duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        
        operations = self.iterations * self.thread_count * 3
        print(f"\nInteger Performance Comparison:")
        print(f"AtomicInt: {operations/safe_duration:,.0f} ops/sec")
        print(f"Normal Int with Lock: {operations/normal_duration:,.0f} ops/sec")
        print(f"Relative Performance: {normal_duration/safe_duration:.2f}x")

    def test_weak_set_performance(self):
        class TestObj:
            pass

        def worker():
            for _ in range(self.iterations):
                obj = TestObj()
                self.weak_set.add(obj)
                _ = obj in self.weak_set
                self.weak_set.remove(obj)
                if _ % 100 == 0:
                    self.weak_set.cleanup()

        threads = [threading.Thread(target=worker) for _ in range(self.thread_count)]
        duration = self.measure_time(lambda: [t.start() for t in threads] or [t.join() for t in threads])
        operations = self.iterations * self.thread_count * 3  # add + contains + remove
        print(f"ThreadSafeWeakSet: {operations/duration:,.0f} ops/sec")


if __name__ == '__main__':
    unittest.main()