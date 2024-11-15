import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from bisq.core.common.user_thread import UserThread
from bisq.log_setup import get_logger
from utils.formatting import readable_file_size
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

logger = get_logger(__name__)

class Statistic:
    """
    Network statistics per connection. As we are also interested in total network statistics
    we use static properties to get traffic of all connections combined.
    """
    # Static Variables
    start_time = time.time()
    total_sent_bytes = 0
    total_received_bytes = 0
    total_sent_messages = defaultdict(int)
    total_received_messages = defaultdict(int)
    num_total_sent_messages = 0
    num_total_received_messages = 0
    total_sent_bytes_per_sec = 0.0
    total_received_bytes_per_sec = 0.0
    num_total_sent_messages_per_sec = 0.0
    num_total_received_messages_per_sec = 0.0

    def __init__(self):
        self.creation_date = datetime.now()
        self.last_activity_timestamp = time.time()
        self.sent_bytes = 0
        self.received_bytes = 0
        self.sent_messages = defaultdict(int)
        self.received_messages = defaultdict(int)
        self.round_trip_time = 0
        # Start periodic updates
        UserThread.run_periodically(self.update_statistics_periodically, timedelta(milliseconds=1))
        UserThread.run_periodically(self.log_statistics_periodically, timedelta(minutes=60))

    def update_statistics_periodically(self):
        Statistic.num_total_sent_messages = sum(Statistic.total_sent_messages.values())
        Statistic.num_total_received_messages = sum(Statistic.total_received_messages.values())
        passed = time.time() - Statistic.start_time
        if passed > 0:
            Statistic.num_total_sent_messages_per_sec = Statistic.num_total_sent_messages / passed
            Statistic.num_total_received_messages_per_sec = Statistic.num_total_received_messages / passed
            Statistic.total_sent_bytes_per_sec = Statistic.total_sent_bytes / passed
            Statistic.total_received_bytes_per_sec = Statistic.total_received_bytes / passed

    def log_statistics_periodically(self):
        logger.info(
            f"Accumulated network statistics:\n"
            f"Bytes sent: {readable_file_size(Statistic.total_sent_bytes)};\n"
            f"Number of sent messages/Sent messages: {Statistic.num_total_sent_messages} / {dict(Statistic.total_sent_messages)};\n"
            f"Number of sent messages per sec: {Statistic.num_total_sent_messages_per_sec};\n"
            f"Bytes received: {readable_file_size(Statistic.total_received_bytes)};\n"
            f"Number of received messages/Received messages: {Statistic.num_total_received_messages} / {dict(Statistic.total_received_messages)};\n"
            f"Number of received messages per sec: {Statistic.num_total_received_messages_per_sec}"
        )


    def update_last_activity_timestamp(self):
        def update():
            self.last_activity_timestamp = get_time_ms()
        UserThread.execute(update)

    def add_sent_bytes(self, value):
        def update():
            self.sent_bytes += value
            Statistic.total_sent_bytes += value
        UserThread.execute(update)

    def add_received_bytes(self, value):
        def update():
            self.received_bytes += value
            Statistic.total_received_bytes += value
        UserThread.execute(update)

    # TODO would need msg inspection to get useful information...
    def add_received_message(self, networkEnvelope: 'NetworkEnvelope'):
        message_class_name = networkEnvelope.__class__.__name__
        def update():
            self.received_messages[message_class_name] += 1
            Statistic.total_received_messages[message_class_name] += 1
        UserThread.execute(update)

    def add_sent_message(self, networkEnvelope: 'NetworkEnvelope'):
        message_class_name = networkEnvelope.__class__.__name__
        def update():
            self.sent_messages[message_class_name] += 1
            Statistic.total_sent_messages[message_class_name] += 1
        UserThread.execute(update)

    def set_round_trip_time(self, round_trip_time):
        def update():
            self.round_trip_time = round_trip_time
        UserThread.execute(update)

    def get_last_activity_age(self):
        return (time.time_ns() // 1_000_000) - self.last_activity_timestamp

    def __str__(self):
        return (
            f"Statistic{{\n"
            f" creationDate={self.creation_date},\n"
            f" lastActivityTimestamp={self.last_activity_timestamp},\n"
            f" sentBytes={self.sent_bytes},\n"
            f" receivedBytes={self.received_bytes},\n"
            f" receivedMessages={dict(self.received_messages)},\n"
            f" sentMessages={dict(self.sent_messages)},\n"
            f" roundTripTime={self.round_trip_time}\n"
            f"}}"
        )