import json
from typing import List

from schema.init_data import Station
from utils import angle_between_lines


def mean(arr):
    return sum(arr) / len(arr)


def get_stations(BASE_DIR) -> List[Station]:
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
    return stations
