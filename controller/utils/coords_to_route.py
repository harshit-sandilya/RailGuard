from typing import List, Tuple
from schema.initial import Track
from schema.gps import Vector3


def distance_from_line_segment(
    point: Tuple[float, float], start: Tuple[float, float], end: Tuple[float, float]
) -> float:
    """
    Calculate the distance from a point to a line segment defined by two points (start and end).
    """
    if start == end:
        return ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5

    line_length_squared = (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2

    if line_length_squared == 0:
        return ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5

    t = (
        (point[0] - start[0]) * (end[0] - start[0])
        + (point[1] - start[1]) * (end[1] - start[1])
    ) / line_length_squared

    if t < 0:
        closest_point = start
    elif t > 1:
        closest_point = end
    else:
        closest_point = (
            start[0] + t * (end[0] - start[0]),
            start[1] + t * (end[1] - start[1]),
        )

    return (
        (point[0] - closest_point[0]) ** 2 + (point[1] - closest_point[1]) ** 2
    ) ** 0.5


def coords_to_route(coords: Vector3, routes: List[List[Track]]) -> int:
    """
    Find the route index that is closest to the given coordinates.

    Args:
        coords: 3D vector coordinates (will use only x and z)
        routes: List of routes, each containing a list of track segments

    Returns:
        Index of the closest route or -1 if routes is empty
    """
    coords_2d = (coords.x / 1000, coords.z / 1000)
    index = -1
    min_distance = float("inf")

    for i, route in enumerate(routes):
        for track in route:
            distance = distance_from_line_segment(
                coords_2d,
                (track.start[0], track.start[1]),
                (track.end[0], track.end[1]),
            )
            if distance < min_distance:
                min_distance = distance
                index = i

    return index
