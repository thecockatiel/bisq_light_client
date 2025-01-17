import threading
import sys
from datetime import datetime
import time
import traceback

def print_active_threads():
    print("-" * 30)
    print("-" * 30)
    print("Active Threads:")
    for thread in threading.enumerate():
        print(f"Thread Name: {thread.name}")
        print(f"Thread ID: {thread.ident}")
        print(f"Is Alive: {thread.is_alive()}")
        print(f"Is Daemon: {thread.daemon}")
        print("-" * 30)
        print("-" * 30)


class ThreadMonitor:
    def __init__(self):
        self.thread_first_seen: dict[int, datetime] = {}
        self.monitoring = False
    
    def capture_thread_state(self):
        current_frames = sys._current_frames()
        thread_info = {}
        
        for thread_id, frame in current_frames.items():
            thread = self._find_thread_by_id(thread_id)
            if thread:
                # Record first time we see this thread
                if thread_id not in self.thread_first_seen:
                    self.thread_first_seen[thread_id] = datetime.now()
                
                stack = traceback.extract_stack(frame)
                thread_info[thread_id] = {
                    'name': thread.name,
                    'stack': ''.join(traceback.format_list(stack)),
                    'first_seen': self.thread_first_seen[thread_id],
                    'daemon': thread.daemon
                }
        return thread_info
    
    def _find_thread_by_id(self, thread_id):
        for thread in threading.enumerate():
            if thread.ident == thread_id:
                return thread
        return None
    
    def print_thread_states(self):
        thread_info = self.capture_thread_state()
        print("\n=== Current Thread States ===")
        for thread_id, info in thread_info.items():
            print(f"\nThread ID: {thread_id}")
            print(f"Thread Name: {info['name']}")
            print(f"First Seen: {info['first_seen']}")
            print(f"Is Daemon: {info['daemon']}")
            print("\nStack Trace:")
            print(info['stack'])
            print("-" * 50)
    
    def start_monitoring(self, interval=1):
        """Start periodic monitoring of threads"""
        self.monitoring = True
        def monitor():
            while self.monitoring:
                self.print_thread_states()
                time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor, 
                                       name="ThreadMonitor",
                                       daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
