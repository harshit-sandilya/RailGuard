import json

from tqdm import tqdm

trains = json.load(open("data/trains.json"))
schedules = json.load(open("data/schedules.json"))
stations = json.load(open("data/stations.json"))

trains = trains["features"]
stations = stations["features"]

train_with_schedule = []
for train in tqdm(trains):
    train_no = train["properties"]["number"]
    train_schedule = []
    train_stations = []
    for schedule in schedules:
        if schedule["train_number"] == train_no:
            train_schedule.append(schedule)
            for station in stations:
                if station["properties"]["code"] == schedule["station_code"]:
                    train_stations.append(station)
    train_with_schedule.append(
        {"train": train, "schedule": train_schedule, "stations": train_stations}
    )

arranged_data = []
for entry in tqdm(train_with_schedule):
    train = entry["train"]
    schedules = entry["schedule"]
    stations = entry["stations"]
    if (
        train["properties"]["number"] is None
        or train["properties"]["name"] is None
        or train["properties"]["type"] is None
        or train["properties"]["distance"] is None
        or train["properties"]["duration_h"] is None
        or train["properties"]["duration_m"] is None
        or train["properties"]["distance"] == 0
        or (
            train["properties"]["duration_h"] == 0
            and train["properties"]["duration_m"] == 0
        )
        or len(schedules) == 0
        or len(stations) == 0
        or len(schedules) == 1
        or len(stations) == 1
    ):
        continue
    arranged_entry = {
        "train_no": 0,
        "train_name": "",
        "type": "",
        "avg_speed": 0,
        "schedule": [],
        "coordinates": [],
    }

    arranged_entry["train_no"] = train["properties"]["number"]
    arranged_entry["train_name"] = train["properties"]["name"]
    arranged_entry["type"] = train["properties"]["type"]
    arranged_entry["avg_speed"] = (
        train["properties"]["distance"]
        / (train["properties"]["duration_h"] * 60 + train["properties"]["duration_m"])
    ) * 60

    for i in range(len(schedules)):
        if (
            (schedules[i]["arrival"] == "None" and schedules[i]["departure"] == "None")
            or stations[i]["geometry"] is None
            or stations[i]["geometry"]["coordinates"] is None
        ):
            continue
        temp_schedule = {
            "station": "",
            "station_code": "",
            "day": 0,
            "arrival": "",
            "departure": "",
        }

        temp_schedule["station"] = schedules[i]["station_name"]
        temp_schedule["station_code"] = schedules[i]["station_code"]
        temp_schedule["day"] = schedules[i]["day"]
        temp_schedule["arrival"] = schedules[i]["arrival"]
        temp_schedule["departure"] = schedules[i]["departure"]

        arranged_entry["schedule"].append(temp_schedule)
        arranged_entry["coordinates"].append(stations[i]["geometry"]["coordinates"])

    if (
        len(arranged_entry["schedule"]) == 0
        or len(arranged_entry["coordinates"]) == 0
        or len(arranged_entry["schedule"]) == 1
        or len(arranged_entry["coordinates"]) == 1
    ):
        continue
    arranged_data.append(arranged_entry)

json.dump(arranged_data, open("data/trains_with_schedules.json", "w"), indent=4)
