from pydantic import BaseModel


class TimerFormat(BaseModel):
    day: int
    hours: int
    minutes: int
    seconds: int

    def __lt__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) < (
            other.day,
            other.hours,
            other.minutes,
            other.seconds,
        )

    def __gt__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) > (
            other.day,
            other.hours,
            other.minutes,
            other.seconds,
        )

    def __eq__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) == (
            other.day,
            other.hours,
            other.minutes,
            other.seconds,
        )

    def __ge__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) >= (
            other.day,
            other.hours,
            other.minutes,
            other.seconds,
        )

    def __le__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) <= (
            other.day,
            other.hours,
            other.minutes,
            other.seconds,
        )

    def __sub__(self, other):
        total_seconds_self = (
            self.day * 86400 + self.hours * 3600 + self.minutes * 60 + self.seconds
        )
        total_seconds_other = (
            other.day * 86400 + other.hours * 3600 + other.minutes * 60 + other.seconds
        )
        diff_seconds = total_seconds_self - total_seconds_other

        days = diff_seconds // 86400
        diff_seconds %= 86400
        hours = diff_seconds // 3600
        diff_seconds %= 3600
        minutes = diff_seconds // 60
        seconds = diff_seconds % 60

        return TimerFormat(day=days, hours=hours, minutes=minutes, seconds=seconds)
