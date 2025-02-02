from pydantic import BaseModel


class TimerFormat(BaseModel):
    day: int
    hours: int
    minutes: int
    seconds: int
