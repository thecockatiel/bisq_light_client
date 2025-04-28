from datetime import timedelta
import threading
import psutil

from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.user_thread import UserThread
from utils.formatting import readable_file_size


class Profiler:
    @staticmethod
    def print_system_load_periodically(delay: timedelta):
        UserThread.run_periodically(Profiler.print_system_load, delay)

    @staticmethod
    def print_system_load():
        logger = get_ctx_logger(__name__)
        logger.info(Profiler.get_system_load())

    @staticmethod
    def get_system_load():
        process = psutil.Process()
        virtual_memory = psutil.virtual_memory()
        total = virtual_memory.total
        free = virtual_memory.available
        used = process.memory_info().rss

        return (
            f"Total memory: {readable_file_size(total)}; Used memory by process: {readable_file_size(used)}; "
            f"Free memory: {readable_file_size(free)}; Max memory: {readable_file_size(total)}; "
            f"No. of threads: {threading.active_count()}"
        )

    @staticmethod
    def get_used_memory_in_mb():
        return Profiler.get_used_memory_in_bytes() / 1024 / 1024

    @staticmethod
    def get_used_memory_in_bytes():
        process = psutil.Process()
        return process.memory_info().rss

    @staticmethod
    def get_free_memory_in_mb():
        return psutil.virtual_memory().available / 1024 / 1024

    @staticmethod
    def get_total_memory_in_mb():
        return psutil.virtual_memory().total / 1024 / 1024
