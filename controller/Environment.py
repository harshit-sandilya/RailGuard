from schema import InitialData


class Environment:
    def __init__(self):
        self.stations = []
        self.tracks = []

    def initialise(self, initData: InitialData):
        self.stations = initData.stations
        self.tracks = initData.tracks
        print(
            f"[Environment] Initialised with {len(self.stations)} stations and {len(self.tracks)} tracks."
        )
