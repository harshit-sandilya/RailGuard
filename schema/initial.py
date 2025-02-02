from pydantic import BaseModel
from typing_extensions import List


class Station(BaseModel):
    name: str
    coords: List[float]
    rotation: float


class InitialData(BaseModel):
    stations: List[Station]
