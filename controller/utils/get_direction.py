from schema.gps import Vector3
from typing import List
from schema.initial import Track


def cosine_of_angle(unit_vector1, unit_vector2):
    dot_product = unit_vector1[0] * unit_vector2[0] + unit_vector1[1] * unit_vector2[1]
    return dot_product / (
        (unit_vector1[0] ** 2 + unit_vector1[1] ** 2) ** 0.5
        * (unit_vector2[0] ** 2 + unit_vector2[1] ** 2) ** 0.5
    )


def get_unit_direction(start_point, end_point):
    direction = (end_point[0] - start_point[0], end_point[1] - start_point[1])
    length = (direction[0] ** 2 + direction[1] ** 2) ** 0.5
    if length == 0:
        return (0, 0)
    return (direction[0] / length, direction[1] / length)


def get_direction(direction: Vector3, route: List[Track]) -> bool:
    point = (direction.x, direction.z)
    track_directions = []
    for track in route:
        track_directions.append(get_unit_direction(track.start, track.end))

    for track_direction in track_directions:
        if cosine_of_angle(track_direction, point) == 1:
            return True
        elif cosine_of_angle(track_direction, point) == -1:
            return False
