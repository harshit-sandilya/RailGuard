import math
from typing import List

from schema.initial import Station, Track


def take_gap(prev, curr, next, gap_distance):
    mid_point1 = ((prev[0] + curr[0]) / 2, (prev[1] + curr[1]) / 2)
    mid_point2 = ((curr[0] + next[0]) / 2, (curr[1] + next[1]) / 2)
    if next[0] - prev[0] == 0:
        # vertical line
        dx = 0
        dy = gap_distance
    elif next[1] - prev[1] == 0:
        # horizontal line
        dx = gap_distance
        dy = 0
    else:
        tan_angle = (next[1] - prev[1]) / (next[0] - prev[0])
        perpendicular_angle = -1 / tan_angle
        dx = math.sqrt(gap_distance**2 / (1 + perpendicular_angle**2))
        dy = perpendicular_angle * dx
    mid_point1 = (mid_point1[0] + dx, mid_point1[1] + dy)
    mid_point2 = (mid_point2[0] + dx, mid_point2[1] + dy)
    return ((prev, mid_point1), (mid_point1, mid_point2), (mid_point2, next))


def add_distance(points, distance):
    point1, point2 = points
    x1, y1 = point1
    x2, y2 = point2
    tan_angle = (y2 - y1) / (x2 - x1)
    dx = math.sqrt(distance**2 / (1 + tan_angle**2))
    dy = tan_angle * dx
    new_point1 = (x1 - dx, y1 - dy)
    new_point2 = (x1 + dx, y1 + dy)
    new_point3 = (x2 - dx, y2 - dy)
    new_point4 = (x2 + dx, y2 + dy)
    return (
        (new_point1, point1),
        (point1, new_point2),
        (new_point2, new_point3),
        (new_point3, point2),
        (point2, new_point4),
    )


def on_line(point, line_start, line_end):
    """Check if a point is on a line segment defined by two endpoints"""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end

    if not (min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)):
        return False
    cross_product = (y - y1) * (x2 - x1) - (x - x1) * (y2 - y1)
    return abs(cross_product) < 1e-9


def filter_track_points(track_points):
    """Filter track points to remove duplicates and sort them"""
    all_points = set()
    for segment in track_points:
        all_points.add(segment[0])
        all_points.add(segment[1])
    all_points = sorted(all_points)

    result = []

    for segment in track_points:
        start, end = segment
        intermediate_points = []

        for point in all_points:
            if point != start and point != end and on_line(point, start, end):
                intermediate_points.append(point)
        if not intermediate_points:
            result.append(segment)
        else:
            intermediate_points.sort(
                key=lambda p: ((p[0] - start[0]) ** 2 + (p[1] - start[1]) ** 2) ** 0.5
            )
            prev_point = start
            for point in intermediate_points:
                result.append((prev_point, point))
                prev_point = point
            result.append((prev_point, end))
    unique_result = set(tuple(sorted((a, b))) for a, b in result)
    return sorted(unique_result)


def generate_tracks(
    stations: List[Station],
    train_data: List[dict],
    train_length: float,
    gap_distance: float,
) -> List[Track]:
    """Returns the list of tracks"""
    tracks_points = [train_data[i]["coordinates"] for i in range(len(train_data))]
    unique_tracks_points = set()
    for track in tracks_points:
        for i in range(len(track) - 1):
            if (tuple(track[i + 1]), tuple(track[i])) not in unique_tracks_points and (
                tuple(track[i]),
                tuple(track[i + 1]),
            ) not in unique_tracks_points:
                unique_tracks_points.add((tuple(track[i]), tuple(track[i + 1])))
    tracks_points = list(unique_tracks_points)
    tracks_points = sorted(tracks_points, key=lambda x: (x[0][0], x[0][1]))
    tracks_points = filter_track_points(tracks_points)
    # print("==============================")
    # print(tracks_points)
    # print("==============================")

    for i in range(len(tracks_points)):
        tracks_points[i] = add_distance(tracks_points[i], train_length)
    # print("==============================")
    # print(tracks_points)
    # print("==============================")
    station_coords = [tuple(station.coords) for station in stations]
    station_segments = set()
    for point in tracks_points:
        if point[1][0] in station_coords:
            # print("==============================")
            # print(point[1][0])
            generated = take_gap(point[0][0], point[1][0], point[2][0], gap_distance)
            station_segments.add(generated)
            # print(generated)
            # print("==============================")
        if point[3][1] in station_coords:
            # print("==============================")
            # print(point[1][0])
            generated = take_gap(point[2][1], point[3][1], point[4][1], gap_distance)
            station_segments.add(generated)
            # print("==============================")
    station_segments = list(station_segments)
    station_segments = sorted(station_segments, key=lambda x: (x[0][0][0], x[0][0][1]))
    # print("==============================")
    # print(station_segments)
    # print("==============================")
    tracks = set()
    for point in tracks_points:
        for pair in point:
            tracks.add(pair)
    for segment in station_segments:
        for pair in segment:
            tracks.add(pair)
    tracks = list(tracks)
    tracks = sorted(tracks, key=lambda x: (x[0], x[1]))
    tracks = [Track(start=track[0], end=track[1]) for track in tracks]
    # print("==============================")
    # print(tracks)
    # print("==============================")
    return tracks
