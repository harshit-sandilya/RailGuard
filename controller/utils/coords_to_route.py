from typing import List
from schema.initial import Track
from schema.gps import Vector3
from .on_line import on_line


def coords_to_route(coords: Vector3, routes: List[List[Track]]) -> int:
    for i in range(len(routes)):
        for track in routes[i]:
            if on_line(
                (coords.x, coords.z),
                (track.start[0], track.start[1]),
                (track.end[0], track.end[1]),
            ):
                return i
