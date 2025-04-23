import json
from typing import List

from schema.initial import InitialData, Station

from .angle_between_lines import angle_between_lines
from .generate_tracks import generate_tracks


def mean(arr):
    return sum(arr) / len(arr)


def get_initial_data(
    train_data: List[dict], BASE_DIR, train_length, station_width
) -> InitialData:
    with open(f"{BASE_DIR}/stations.json") as f:
        stations = json.load(f)
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
    tracks = generate_tracks(
        stations,
        train_data,
        (train_length * 2) / 1000,
        (station_width * 4) / 1000,
    )
    data = InitialData(stations=stations, tracks=tracks)
    return data
