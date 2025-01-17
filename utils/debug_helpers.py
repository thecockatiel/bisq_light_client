import threading


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
