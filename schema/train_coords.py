from typing import List

from pydantic import BaseModel


class TrainCoords(BaseModel):
    number: int
    speed: float
    current_coords: List[float]
    rotation: float
