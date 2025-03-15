import json

train_data = json.load(open("data/generated_trains.json"))

tracks = set()

for train in train_data:
    for i in range(len(train["coordinates"]) - 1):
        coord1, coord2 = tuple(train["coordinates"][i]), tuple(
            train["coordinates"][i + 1]
        )
        if (coord2, coord1) not in tracks:
            tracks.add((coord1, coord2))

tracks = list(tracks)
tracks_json = [{"start": coord1, "end": coord2} for coord1, coord2 in tracks]

json.dump(tracks_json, open("data/generated_tracks.json", "w"))
