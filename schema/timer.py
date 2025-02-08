from pydantic import BaseModel


class TimerFormat(BaseModel):
    day: int
    hours: int
    minutes: int
    seconds: int

    def __lt__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) < (other.day, other.hours, other.minutes, other.seconds)

    def __gt__(self, other):
        return (self.day, self.hours, self.minutes, self.seconds) > (other.day, other.hours, other.minutes, other.seconds)
