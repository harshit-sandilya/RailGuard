from schema.timer import TimerFormat


def str_to_timer(day: int, time_str: str) -> TimerFormat:
    hour, minute, second = map(int, time_str.split(":"))
    return TimerFormat(day=day, hours=hour, minutes=minute, seconds=second)
