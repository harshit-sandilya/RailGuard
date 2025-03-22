import json

from schema import InitialData
from typing import List
from configObject import config
from schema.initial import Station, Track
from preprocess.generate_tracks import get_tracks
from utils.angle_between_lines import angle_between_lines
from pprint import pprint


def mean(arr):
    return sum(arr) / len(arr)


def get_initial_data(train_data: List[dict], BASE_DIR) -> InitialData:
    no_trains = len(train_data)
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
    tracks = get_tracks(stations, train_data, config.train.length/1000, config.station.width * 2/1000)
    data = InitialData(stations=stations, tracks=tracks, trains=no_trains)
    pprint(data.tracks)
    return data
