from schema import InitialData, TrainObject, GPSData
from .utils import group_tracks_into_branches, coords_to_route, get_direction


class Environment:
    def __init__(self):
        self.stations = []
        self.tracks = []
        self.trains = []

    def initialise(self, initData: InitialData):
        self.stations = initData.stations
        self.tracks = group_tracks_into_branches(initData.tracks)
        print(
            f"[Environment] Initialised with {len(self.stations)} stations and {len(self.tracks)} tracks."
        )

    def initialise_trains(self, num_trains):
        self.trains = [TrainObject() for _ in range(num_trains)]
        print(f"[Environment] Initialised with {len(self.trains)} trains.")

    def update_train(self, index, gpsData: GPSData):
        self.trains[index].curr_segment = coords_to_route(gpsData.coords, self.tracks)
        self.trains[index].distance_remaining = gpsData.distanceRemaining
        self.trains[index].speed = gpsData.speed
        self.trains[index].delay = gpsData.delay
        self.trains[index].direction = get_direction(
            gpsData.direction, self.tracks[self.trains[index].curr_segment]
        )
        print(f"[Environment] Updated train {index} with GPS data.")
