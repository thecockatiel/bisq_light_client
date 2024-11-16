import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from bisq.core.common.user_thread import UserThread
from bisq.log_setup import get_logger
from utils.concurrency import ThreadSafeDict
from utils.data import SimpleProperty
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
    start_time = get_time_ms()
    total_sent_bytes = SimpleProperty(0)
    total_received_bytes = SimpleProperty(0)
    total_sent_messages: ThreadSafeDict[str, int] = ThreadSafeDict()
    total_received_messages: ThreadSafeDict[str, int] = ThreadSafeDict()
    num_total_sent_messages = SimpleProperty(0)
    num_total_received_messages = SimpleProperty(0)
    total_sent_bytes_per_sec = SimpleProperty(0.0)
    total_received_bytes_per_sec = SimpleProperty(0.0)
    num_total_sent_messages_per_sec = SimpleProperty(0.0)
    num_total_received_messages_per_sec = SimpleProperty(0.0)

    def __init__(self):
        self.creation_date = datetime.now()
        self.last_activity_timestamp = get_time_ms()
        self.sent_bytes = SimpleProperty(0)
        self.received_bytes = SimpleProperty(0)
        self.sent_messages: ThreadSafeDict[str, int] = ThreadSafeDict()
        self.received_messages: ThreadSafeDict[str, int] = ThreadSafeDict()
        self.round_trip_time = SimpleProperty(0)
        # Start periodic updates
        UserThread.run_periodically(self._update_statistics_periodically, timedelta(seconds=1))
        UserThread.run_periodically(self._log_statistics_periodically, timedelta(minutes=60))

    def _update_statistics_periodically(self):
        Statistic.num_total_sent_messages.value = sum(Statistic.total_sent_messages.values())
        Statistic.num_total_received_messages.value = sum(Statistic.total_received_messages.values())
        passed = get_time_ms() - Statistic.start_time
        if passed > 0:
            Statistic.num_total_sent_messages_per_sec.value = Statistic.num_total_sent_messages.value / passed
            Statistic.num_total_received_messages_per_sec.value = Statistic.num_total_received_messages.value / passed
            Statistic.total_sent_bytes_per_sec.value = Statistic.total_sent_bytes.value / passed
            Statistic.total_received_bytes_per_sec.value = Statistic.total_received_bytes.value / passed

    def _log_statistics_periodically(self):
        logger.info(
            f"Accumulated network statistics:\n"
            f"Bytes sent: {readable_file_size(Statistic.total_sent_bytes.value)};\n"
            f"Number of sent messages/Sent messages: {Statistic.num_total_sent_messages.value} / {dict(Statistic.total_sent_messages)};\n"
            f"Number of sent messages per sec: {Statistic.num_total_sent_messages_per_sec.value};\n"
            f"Bytes received: {readable_file_size(Statistic.total_received_bytes.value)};\n"
            f"Number of received messages/Received messages: {Statistic.num_total_received_messages.value} / {dict(Statistic.total_received_messages)};\n"
            f"Number of received messages per sec: {Statistic.num_total_received_messages_per_sec.value}"
        )


    def update_last_activity_timestamp(self):
        def update():
            self.last_activity_timestamp = get_time_ms()
        UserThread.execute(update)

    def add_sent_bytes(self, value):
        def update():
            self.sent_bytes.value += value
            Statistic.total_sent_bytes.value += value
        UserThread.execute(update)

    def add_received_bytes(self, value):
        def update():
            self.received_bytes.value += value
            Statistic.total_received_bytes.value += value
        UserThread.execute(update)

    # TODO would need msg inspection to get useful information...
    def add_received_message(self, networkEnvelope: 'NetworkEnvelope'):
        message_class_name = networkEnvelope.__class__.__name__
        def update():
            self.received_messages.get_and_put(message_class_name, lambda v: v+1)
            Statistic.total_received_messages.get_and_put(message_class_name, lambda v: v+1)
        UserThread.execute(update)

    def add_sent_message(self, networkEnvelope: 'NetworkEnvelope'):
        message_class_name = networkEnvelope.__class__.__name__
        def update():
            self.sent_messages.get_and_put(message_class_name, lambda v: v+1)
            Statistic.total_sent_messages.get_and_put(message_class_name, lambda v: v+1)
        UserThread.execute(update)

    def set_round_trip_time(self, round_trip_time: int):
        def update():
            self.round_trip_time.value = round_trip_time
        UserThread.execute(update)

    def get_last_activity_age(self):
        return get_time_ms() - self.last_activity_timestamp

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