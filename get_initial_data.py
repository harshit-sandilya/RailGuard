import json

from schema import InitialData
from schema.initial import Station, Track
from utils.angle_between_lines import angle_between_lines


def mean(arr):
    return sum(arr) / len(arr)


def get_initial_data() -> InitialData:
    with open("data/generated_stations.json") as f:
        stations = json.load(f)
    with open("data/generated_tracks.json") as f:
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
    data = InitialData(stations=stations, tracks=tracks)
    print("Initial data loaded",data.tracks)
    return data
