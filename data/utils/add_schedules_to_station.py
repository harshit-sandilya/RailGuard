import json

from tqdm import tqdm

trains = json.load(open("data/trains.json"))
schedules = json.load(open("data/schedules.json"))
stations = json.load(open("data/stations.json"))

trains = trains["features"]
stations = stations["features"]

station_with_schedule = []
for station in tqdm(stations):
    station_code = station["properties"]["code"]
    station_schedule = []
    station_trains = []
    for schedule in schedules:
        if schedule["station_code"] == station_code:
            station_schedule.append(schedule)
            for train in trains:
                if train["properties"]["number"] == schedule["train_number"]:
                    station_trains.append(train["properties"])
    station_with_schedule.append(
        {"station": station, "schedule": station_schedule, "trains": station_trains}
    )

arranged_data = []
for entry in tqdm(station_with_schedule):
    trains = entry["trains"]
    schedules = entry["schedule"]
    station = entry["station"]
    if (
        station["properties"]["name"] is None
        or station["properties"]["code"] is None
        or station["properties"]["state"] is None
        or len(trains) == 0
        or len(schedules) == 0
        or station["geometry"] is None
        or station["geometry"]["coordinates"] is None
    ):
        continue
    arranged_entry = {
        "station": "",
        "station_code": "",
        "state": "",
        "schedule": [],
        "coordinates": [],
    }
    arranged_entry["station"] = station["properties"]["name"]
    arranged_entry["station_code"] = station["properties"]["code"]
    arranged_entry["state"] = station["properties"]["state"]
    arranged_entry["coordinates"] = station["geometry"]["coordinates"]
    for i in range(len(schedules)):
        if (
            (schedules[i]["arrival"] == "None" and schedules[i]["departure"] == "None")
            or trains[i]["number"] is None
            or trains[i]["name"] is None
            or trains[i]["type"] is None
            or trains[i]["distance"] is None
            or trains[i]["duration_h"] is None
            or trains[i]["duration_m"] is None
            or trains[i]["distance"] == 0
            or (trains[i]["duration_h"] == 0 and trains[i]["duration_m"] == 0)
        ):
            continue
        temp_schedule = {
            "train_no": 0,
            "train_name": "",
            "type": "",
            "avg_speed": 0,
            "arrival": "",
            "departure": "",
            "day": 0,
        }
        temp_schedule["train_no"] = trains[i]["number"]
        temp_schedule["train_name"] = trains[i]["name"]
        temp_schedule["type"] = trains[i]["type"]
        temp_schedule["avg_speed"] = (
            trains[i]["distance"]
            / (trains[i]["duration_h"] * 60 + trains[i]["duration_m"])
        ) * 60
        temp_schedule["arrival"] = schedules[i]["arrival"]
        temp_schedule["departure"] = schedules[i]["departure"]
        temp_schedule["day"] = schedules[i]["day"]
        arranged_entry["schedule"].append(temp_schedule)
    if len(arranged_entry["schedule"]) > 0:
        arranged_data.append(arranged_entry)

json.dump(arranged_data, open("data/stations_with_schedules.json", "w"), indent=4)
