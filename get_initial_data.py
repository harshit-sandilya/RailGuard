import json

from schema import InitialData
from schema.initial import Station, Track
from utils.angle_between_lines import angle_between_lines
from constants import TIME_SECOND, DAY_HOURS


def mean(arr):
    return sum(arr) / len(arr)


def get_initial_data(no_trains: int, BASE_DIR) -> InitialData:
    with open(f"{BASE_DIR}/stations.json") as f:
        stations = json.load(f)
    with open(f"{BASE_DIR}/tracks.json") as f:
        tracks = json.load(f)
    data = []
    for station in stations:
        data.append({"name": station["station"], "coords": station["coordinates"]})
    center = [
        mean([entry["coords"][0] for entry in data]),
        mean([entry["coords"][1] for entry in data]),
    ]
    for entry in data:
        entry["rotation"] = angle_between_lines(
            center, entry["coords"], entry["coords"], (center[0], entry["coords"][1])
        )
    stations = [Station(**entry) for entry in data]
    tracks = [Track(**entry) for entry in tracks]
    data = InitialData(stations=stations, tracks=tracks, trains=no_trains, TIME_SECOND=TIME_SECOND, DAY_HOURS=DAY_HOURS)
    print("Initial data loaded", data.tracks)
    return data
