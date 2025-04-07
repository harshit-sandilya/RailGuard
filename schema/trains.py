from pydantic import BaseModel


class TrainObject(BaseModel):
    curr_segment: int
    distance_remaining: float
    speed: float
    delay: int
    direction: int

    def __init__(self, **data):
        defaults = {
            "curr_segment": -1,
            "distance_remaining": 0,
            "speed": 0,
            "delay": 0,
            "direction": 0,
        }

        defaults.update(data)
        super().__init__(**defaults)
