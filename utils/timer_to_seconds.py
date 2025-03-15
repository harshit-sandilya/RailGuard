from schema.timer import TimerFormat


def timer_to_seconds(time: TimerFormat) -> int:
    return time.seconds + time.minutes * 60 + time.hours * 3600 + time.day * 86400
