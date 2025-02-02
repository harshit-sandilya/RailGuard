import json
from typing import List

from typing_extensions import Optional

from schema import TimerFormat, TrainCoords
from utils import angle_between_lines

train_data = json.load(open("data/generated_trains.json"))
train_numbers = []

for index, train in enumerate(train_data):
    train["index"] = index
    train_numbers.append(train["train_no"])

train_dict = {train["train_no"]: train for train in train_data}

# trips = [0*len(train_data)]
from_index = [0] * len(train_data)
to_index = [1] * len(train_data)
day_hours = 5
train_data = None


def get_first_time_of_day(schedules: List, day) -> str:
    for schedule in schedules:
        if schedule["arrival_day"] == day:
            return schedule["arrival"]
    return schedules[0]["arrival"]


def is_in_range(schedules: List, curr_time) -> bool:
    schedule = schedules[-1]
    if schedule["departure_day"] <= curr_time.day:
        return compare_time_smaller(curr_time, schedule["departure"])
    return True


def find_distance(coords1: List[int], coords2: List[int]) -> float:
    return ((coords1[0] - coords2[0]) ** 2 + (coords1[1] - coords2[1]) ** 2) ** 0.5


def find_time_diff(time1: str, time2: str, day1, day2) -> float:
    hours1, minutes1, seconds1 = map(int, time1.split(":"))
    hours2, minutes2, seconds2 = map(int, time2.split(":"))
    diff = (
        (day1 - day2) * day_hours
        + (hours1 - hours2) * 3600
        + (minutes1 - minutes2) * 60
        + (seconds1 - seconds2)
    ) / 3600
    return diff


def find_time_diff_with_obj(time1: TimerFormat, time2: str, day1, day2) -> float:
    hours1, minutes1, seconds1 = time1.hours, time1.minutes, time1.seconds
    hours2, minutes2, seconds2 = map(int, time2.split(":"))
    diff = (
        (day1 - day2) * day_hours
        + (hours1 - hours2) * 3600
        + (minutes1 - minutes2) * 60
        + (seconds1 - seconds2)
    ) / 3600
    return diff


def compare_time_greater(time1: TimerFormat, time2: str) -> bool:
    if (
        time1.hours >= int(time2.split(":")[0])
        and time1.minutes >= int(time2.split(":")[1])
        and time1.seconds >= int(time2.split(":")[2])
    ):
        return True
    return False


def compare_time_smaller(time1: TimerFormat, time2: str) -> bool:
    if (
        time1.hours <= int(time2.split(":")[0])
        and time1.minutes <= int(time2.split(":")[1])
        and time1.seconds <= int(time2.split(":")[2])
    ):
        return True
    return False


def get_coords_of_trains(
    curr_time: TimerFormat, train_no: int
) -> Optional[TrainCoords]:
    train = train_dict[train_no]
    index = train["index"]
    if compare_time_greater(
        curr_time, get_first_time_of_day(train["schedules"], curr_time.day)
    ) and is_in_range(train["schedules"], curr_time):
        from_coords = train["coordinates"][from_index[index]]
        to_coords = train["coordinates"][to_index[index]]
        speed = find_distance(from_coords, to_coords) / find_time_diff(
            train["schedules"][to_index[index]]["arrival"],
            train["schedules"][from_index[index]]["departure"],
            train["schedules"][to_index[index]]["arrival_day"],
            train["schedules"][from_index[index]]["departure_day"],
        )
        distance_covered = speed * find_time_diff_with_obj(
            curr_time,
            train["schedules"][from_index[index]]["departure"],
            curr_time.day,
            train["schedules"][from_index[index]]["departure_day"],
        )
        direction_vector = [
            to_coords[0] - from_coords[0],
            to_coords[1] - from_coords[1],
        ]
        direction_vector = [
            direction_vector[0] / find_distance(from_coords, to_coords),
            direction_vector[1] / find_distance(from_coords, to_coords),
        ]
        distance_vector = [
            direction_vector[0] * distance_covered,
            direction_vector[1] * distance_covered,
        ]
        curr_coords = [
            from_coords[0] + distance_vector[0],
            from_coords[1] + distance_vector[1],
        ]
        rotation = angle_between_lines(
            from_coords, to_coords, to_coords, [from_coords[0], to_coords[1]]
        )
        if curr_coords[0] > to_coords[0] and curr_coords[1] > to_coords[1]:
            curr_coords = to_coords
            from_index[index] = to_index[index]
            to_index[index] = (to_index[index] + 1) % len(train["coordinates"])
        return TrainCoords(
            number=train["train_no"],
            speed=speed,
            current_coords=curr_coords,
            rotation=rotation,
        )
    else:
        return None
