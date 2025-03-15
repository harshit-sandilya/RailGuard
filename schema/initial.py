from pydantic import BaseModel
from typing_extensions import List


class Station(BaseModel):
    name: str
    coords: List[float]
    rotation: float


class Track(BaseModel):
    start: List[float]
    end: List[float]


class InitialData(BaseModel):
    stations: List[Station]
    tracks: List[Track]
    trains: int
    TIME_SECOND: float
    DAY_HOURS: int
