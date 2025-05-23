from dataclasses import dataclass
import time


@dataclass(frozen=True)
class Clock:
    def millis(self):
        # Convert nanoseconds to milliseconds using floor division
        time_ms = time.time_ns() // 1_000_000
        return time_ms
