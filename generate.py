import json
import math
import random
from random import choice
from string import ascii_uppercase

NUM_STATIONS = 3
NUM_TRAINS = 2
frac_combinations = 0.75
day_hours = 4

station_schedules = {
    "train_no": 0,
    "train_name": "",
    "type": "",
    "avg_speed": 0,
    "arrival": "",
    "departure": "",
    "day": 0,
}

stations = []
trains = []

for i in range(NUM_STATIONS):
    station = {
        "station": "",
        "station_code": "",
        "state": "",
        "schedules": [],
        "coordinates": [0, 0],
    }
    len_str = random.randint(3, 10)
    station["station"] = "".join(choice(ascii_uppercase) for _ in range(len_str))
    station["station_code"] = station["station"][:3]
    station["state"] = "".join(choice(ascii_uppercase) for _ in range(11))
    coords = [0, 0]
    coords[0] = random.randint(len_str * 5, 200)
    coords[1] = random.randint(len_str * 2, 200)
    station["coordinates"] = coords
    stations.append(station)

# STATIONS GENERTED WITHOUT SCHEDULES

for i in range(NUM_TRAINS):
    train = {
        "train_no": 0,
        "train_name": "",
        "type": "",
        "avg_speed": 0,
        "schedules": [],
        "coordinates": [],
    }
    train["train_no"] = random.randint(10000, 99999)
    len_str = random.randint(5, 20)
    train["train_name"] = "".join(choice(ascii_uppercase) for _ in range(len_str))
    train["type"] = "".join(choice(ascii_uppercase) for _ in range(5))
    trains.append(train)

# TRAINS GENERATED WITHOUT SCHEDULES

max_combinations = math.factorial(NUM_STATIONS) / (
    math.factorial(NUM_STATIONS - 2) * math.factorial(2)
)

combinations = math.ceil(frac_combinations * max_combinations)

start_stations = []
end_stations = []
for i in range(combinations):
    start_stations.append(random.randint(0, NUM_STATIONS - 1))
    end = random.randint(0, NUM_STATIONS - 1)
    while end == start_stations[i]:
        end = random.randint(0, NUM_STATIONS - 1)
    end_stations.append(end)

combinations_list = [[start_stations[i], end_stations[i]] for i in range(combinations)]
combinations_list = [
    random.sample(combination, len(combination)) for combination in combinations_list
]
combinations = len(combinations_list)

while combinations < NUM_TRAINS:
    combinations_list.append(random.sample(combinations_list, k=1)[0])
    combinations = len(combinations_list)

schedules = []
for combination in combinations_list:
    remaining_stations = list(range(NUM_STATIONS))
    remaining_stations.remove(combination[0])
    remaining_stations.remove(combination[1])
    num_remaining_stations = len(remaining_stations)
    no_stations = random.randint(0, num_remaining_stations)
    stations_list = [combination[0]]
    for i in range(no_stations):
        stations_list.append(random.choice(remaining_stations))
        remaining_stations.remove(stations_list[-1])
    stations_list.append(combination[1])
    schedules.append(stations_list)

# PATHS GENERATED FOR TRAINS


def process_time(time, hour, minute, day):
    add_hour = int(time)
    add_minute = int((time - add_hour) * 60)
    hour = hour + add_hour
    minute = minute + add_minute
    while minute >= 60:
        minute = minute - 60
        hour = hour + 1
    while hour >= day_hours:
        hour = hour - day_hours
        day = day + 1
    return hour, minute, day


for i, train in enumerate(trains):
    train["schedules"] = []
    train["coordinates"] = []
    avg_speed = random.randint(50, 100)
    train["avg_speed"] = avg_speed
    prev_schedule = None

    hour = 0
    minute = 0
    day = 0

    for j, station in enumerate(schedules[i]):
        station = stations[station]
        train_schedule = {
            "station": "",
            "station_code": "",
            "arrival_day": 0,
            "departure_day": 0,
            "arrival": "",
            "departure": "",
        }
        station_schedule = {
            "train_no": "",
            "train_name": "",
            "type": "",
            "avg_speed": 0,
            "arrival": "",
            "departure": "",
            "arrival_day": 0,
            "departure_day": 0,
        }
        train_schedule["station"] = station["station"]
        train_schedule["station_code"] = station["station_code"]
        station_schedule["train_no"] = train["train_no"]
        station_schedule["train_name"] = train["train_name"]
        station_schedule["type"] = train["type"]
        station_schedule["avg_speed"] = train["avg_speed"]

        if j == 0:
            hour = random.randint(0, day_hours)
            minute = random.randint(0, 59)
            train_schedule["arrival_day"] = 0
            station_schedule["arrival_day"] = 0
            train_schedule["departure"] = f"{hour}:{minute}:00"
            station_schedule["departure"] = f"{hour}:{minute}:00"
            train_schedule["arrival"] = f"{hour}:{minute}:00"
            station_schedule["arrival"] = f"{hour}:{minute}:00"
            train_schedule["departure_day"] = day
            station_schedule["departure_day"] = day
        else:
            avg_speed = random.randint(
                trains[i]["avg_speed"] - 20, trains[i]["avg_speed"] + 20
            )
            initial_point = train["coordinates"][-1]
            final_point = station["coordinates"]
            distance = math.sqrt(
                (final_point[0] - initial_point[0]) ** 2
                + (final_point[1] - initial_point[1]) ** 2
            )
            time = distance / avg_speed
            hour, minute, day = process_time(time, hour, minute, day)
            train_schedule["arrival"] = f"{hour}:{minute}:00"
            station_schedule["arrival"] = f"{hour}:{minute}:00"
            train_schedule["arrival_day"] = day
            station_schedule["arrival_day"] = day
            minute = minute + random.randint(2, 10)
            if minute >= 60:
                minute = minute - 60
                hour = hour + 1
            if hour >= day_hours:
                hour = hour - day_hours
                day = day + 1
            train_schedule["departure"] = f"{hour}:{minute}:00"
            station_schedule["departure"] = f"{hour}:{minute}:00"
            train_schedule["departure_day"] = day
            station_schedule["departure_day"] = day
        train["schedules"].append(train_schedule)
        station["schedules"].append(station_schedule)
        train["coordinates"].append(station["coordinates"])

# SCHEDULES GENERATED FOR TRAINS

with open("./data/generated_trains.json", "w") as trains_file:
    json.dump(trains, trains_file, indent=4)

with open("./data/generated_stations.json", "w") as stations_file:
    json.dump(stations, stations_file, indent=4)
