from typing import List
from schema.initial import Track


def point_to_tuple(point):
    return tuple(point)


def group_tracks_into_branches(tracks: List[Track]) -> List[List[Track]]:
    outgoing_tracks = {}
    incoming_tracks = {}

    for track in tracks:
        start_tuple = point_to_tuple(track.start)
        end_tuple = point_to_tuple(track.end)

        if start_tuple not in outgoing_tracks:
            outgoing_tracks[start_tuple] = []
        outgoing_tracks[start_tuple].append(track)

        if end_tuple not in incoming_tracks:
            incoming_tracks[end_tuple] = []
        incoming_tracks[end_tuple].append(track)

    branch_start_points = set()
    for point in set(outgoing_tracks.keys()).union(set(incoming_tracks.keys())):
        in_count = len(incoming_tracks.get(point, []))
        out_count = len(outgoing_tracks.get(point, []))

        if in_count == 0 or out_count > 1 or in_count > 1:
            branch_start_points.add(point)

    branches = []
    visited_tracks = set()

    def follow_branch(current_track, branch):
        visited_tracks.add(id(current_track))
        branch.append(current_track)

        end_point = point_to_tuple(current_track.end)

        out_tracks = outgoing_tracks.get(end_point, [])
        in_tracks = incoming_tracks.get(end_point, [])

        if len(out_tracks) == 1 and len(in_tracks) == 1:
            next_track = out_tracks[0]
            if id(next_track) not in visited_tracks:
                follow_branch(next_track, branch)

    for start_point in branch_start_points:
        for track in outgoing_tracks.get(start_point, []):
            if id(track) not in visited_tracks:
                new_branch = []
                follow_branch(track, new_branch)
                branches.append(new_branch)

    for track in tracks:
        if id(track) not in visited_tracks:
            new_branch = []
            follow_branch(track, new_branch)
            branches.append(new_branch)

    branches.sort(key=lambda branch: point_to_tuple(branch[0].start))

    return branches
