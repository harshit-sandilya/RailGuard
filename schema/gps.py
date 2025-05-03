from pydantic import BaseModel


class Vector3(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class GPSData(BaseModel):
    coords: Vector3
    segment: int
    next_segment: int
    speed: float = 0.0
    distanceRemaining: float = 0.0
    direction: int
