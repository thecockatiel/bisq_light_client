import re
import math
import textwrap

# Pre-compile regex patterns for performance
pattern_one_second = re.compile(r"(^|\b)1 seconds")
pattern_one_minute = re.compile(r"(^|\b)1 minutes")
pattern_one_hour = re.compile(r"(^|\b)1 hours")
pattern_one_day = re.compile(r"(^|\b)1 days")
pattern_zero_days = re.compile(r"^0 days, ")
pattern_zero_hours = re.compile(r"^0 hours, ")
pattern_zero_minutes = re.compile(r"^0 minutes, ")
pattern_zero_seconds = re.compile(r"^0 seconds, ")

def format_duration_as_words(duration_millis):
    second = "second"
    minute = "minute"
    hour = "hour"
    day = "day"
    days_str = "days"
    hours_str = "hours"
    minutes_str = "minutes"
    seconds_str = "seconds"

    duration_millis = int(duration_millis)
    days = duration_millis // 86400000
    remainder = duration_millis % 86400000
    hours = remainder // 3600000
    remainder %= 3600000
    minutes = remainder // 60000
    remainder %= 60000
    seconds = remainder // 1000
    milliseconds = remainder % 1000

    if duration_millis >= 86400000:
        format_str = "%d " + days_str + ", %d " + hours_str + ", %d " + minutes_str + ", %d.%03d " + seconds_str
        duration = format_str % (days, hours, minutes, seconds, milliseconds)
    else:
        format_str = "%d " + hours_str + ", %d " + minutes_str + ", %d.%03d " + seconds_str
        duration = format_str % (hours, minutes, seconds, milliseconds)

    # Replace plural with singular where appropriate
    duration = pattern_one_second.sub(r"\g<1>1 " + second, duration)
    duration = pattern_one_minute.sub(r"\g<1>1 " + minute, duration)
    duration = pattern_one_hour.sub(r"\g<1>1 " + hour, duration)
    duration = pattern_one_day.sub(r"\g<1>1 " + day, duration)

    # Remove segments with zero values
    duration = duration.replace(", 0 " + seconds_str, "")
    duration = duration.replace(", 0 " + minutes_str, "")
    duration = duration.replace(", 0 " + hours_str, "")
    duration = pattern_zero_days.sub("", duration)
    duration = pattern_zero_hours.sub("", duration)
    duration = pattern_zero_minutes.sub("", duration)
    duration = pattern_zero_seconds.sub("", duration)

    result = duration.strip()
    if not result:
        result = "0.000 seconds"
    return result

def readable_file_size(size):
    if size <= 0:
        return "0"
    units = ["B", "kB", "MB", "GB", "TB"]
    digit_groups = int(math.log10(size) / math.log10(1024))
    digit_groups = min(digit_groups, len(units) - 1)
    size_in_units = size / math.pow(1024, digit_groups)
    formatted_size = '{:,.3f}'.format(size_in_units).rstrip('0').rstrip('.')
    return f"{formatted_size} {units[digit_groups]}"

def to_truncated_string(message, max_length=200, remove_line_breaks=True):
    if message is None:
        return "null"

    result = message
    if not isinstance(result, str):
        result = str(message)
    
    if max_length > 3:
        result = result[:max_length - 3] + '...' if len(result) > max_length else result
    else:
        result = result[:max_length]

    if remove_line_breaks:
        result = result.replace("\n", "")

    return result

def get_short_id(id: str, sep='-'):
    if not id: return "None"
    chunks = id.split(sep)
    if len(chunks) > 1: # NOTE: incorrect logic in in original bisq. Should be > 1, not > 0, but I don't know if it's intentional
        return chunks[0]
    else:
        return id[:min(8, len(id))]
