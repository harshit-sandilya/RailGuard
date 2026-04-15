from pydantic import BaseModel


class Control(BaseModel):
    next_segment: int
    next_halt_time: int
