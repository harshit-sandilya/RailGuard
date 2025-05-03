from pydantic import BaseModel


class TrainObject(BaseModel):
    curr_segment: int
    next_segment: int
    speed: float
    distance_remaining: float
    direction: int
    last_updated: int

    def __init__(self, **data):
        defaults = {
            "curr_segment": 7,
            "next_segment": 7,
            "speed": 0,
            "distance_remaining": 0,
            "direction": 0,
            "last_updated": 0,
        }

        defaults.update(data)
        super().__init__(**defaults)
