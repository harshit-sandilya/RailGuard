from typing import List

from pydantic import BaseModel


class TrainData(BaseModel):
    number: int
    start_coords: List[float]
    end_coords: List[float]
    time_allocated: float
    halt_time: float
