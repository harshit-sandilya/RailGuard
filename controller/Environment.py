from typing import List

import numpy as np

from schema import GPSData, InitialData, TrainObject
from utils import coords_to_route, get_direction, group_tracks_into_branches


class Environment:
    def __init__(self):
        self.stations = []
        self.tracks = []
        self.trains: List[TrainObject] = []

    def initialise(self, initData: InitialData):
        self.stations = initData.stations
        self.tracks = group_tracks_into_branches(initData.tracks)
        print(
            f"[CONTROLLER: ENVIRONMENT] Initialised with {len(self.stations)} stations and {len(self.tracks)} tracks."
        )

    def initialise_trains(self, num_trains):
        self.trains = [TrainObject() for _ in range(num_trains)]
        print(f"[CONTROLLER: ENVIRONMENT] Initialised with {len(self.trains)} trains.")

    def update_train(self, index, gpsData: GPSData):
        self.trains[index].curr_segment = coords_to_route(gpsData.coords, self.tracks)
        self.trains[index].distance_remaining = gpsData.distanceRemaining
        self.trains[index].speed = gpsData.speed
        self.trains[index].delay = gpsData.delay
        self.trains[index].direction = get_direction(
            gpsData.direction, self.tracks[self.trains[index].curr_segment]
        )

    def get_observation(self) -> np.array:
        observations = []
        for train in self.trains:
            curr_segment = train.curr_segment
            distance_remaining = train.distance_remaining
            observation = np.array(
                [
                    curr_segment,
                    distance_remaining,
                    train.speed,
                    train.delay,
                    train.direction,
                ]
            )
            observations.append(observation)

        return np.array(observations)

    def process_action(self, action):
        pass
