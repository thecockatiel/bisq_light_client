from datetime import timezone, timedelta
import time

class Clock:
    
    def __init__(self, td: timedelta = None, tz: timezone = None):
        self.tz = tz
        self.td = td

    def millis(self):
        # Convert nanoseconds to milliseconds using floor division
        time_ms = time.time_ns() // 1_000_000
        # add the offset
        if self.td != None:
            time_ms = time_ms + self.td.total_seconds() * 1000
        return time_ms

    @staticmethod
    def systemDefaultZone():
        return Clock()

    @staticmethod
    def offset(clock: 'Clock', offset: timedelta):
        return Clock(td=offset, tz=clock.tz)
