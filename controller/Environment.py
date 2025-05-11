import socket
import threading
from typing import List

import numpy as np

from schema import Control, GPSData, InitialData, TrainObject
from utils import group_tracks_into_branches


class Environment:
    def __init__(self, port, timer):
        self.stations = []
        self.tracks = []
        self.trains: List[TrainObject] = []
        self.no_trains = 0
        self.no_stations = 0
        self.port = port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.multicast_groups = []
        self.timer = timer

    def create_adjacency_list(self):
        self.adjacency_list = [[] for _ in range(len(self.tracks))]

        for i in range(len(self.tracks)):
            segment_start = (self.tracks[i][0].start[0], self.tracks[i][0].start[1])
            segment_end = (self.tracks[i][-1].end[0], self.tracks[i][-1].end[1])

            for j in range(len(self.tracks)):
                if i != j:
                    other_segment_start = (
                        self.tracks[j][0].start[0],
                        self.tracks[j][0].start[1],
                    )
                    other_segment_end = (
                        self.tracks[j][-1].end[0],
                        self.tracks[j][-1].end[1],
                    )

                    if (
                        segment_start == other_segment_end
                        or segment_end == other_segment_start
                    ):
                        self.adjacency_list[i].append(j)

        self.adjacency_list[0].append(7)
        self.adjacency_list[6].append(7)

    def initialise(self, initData: InitialData):
        self.stations = initData.stations
        self.tracks = group_tracks_into_branches(initData.tracks)
        self.no_stations = len(self.stations)
        self.create_adjacency_list()
        print(
            f"[CONTROLLER: ENVIRONMENT] Initialised with {len(self.stations)} stations and {len(self.tracks)} tracks."
        )

    def initialise_trains(self, num_trains):
        self.trains = [TrainObject() for _ in range(num_trains)]
        self.no_trains = num_trains
        self.multicast_groups = [
            ("224.0.0.1", self.port + i) for i in range(num_trains)
        ]
        self.isRunning = [False] * num_trains
        self.update_thread = threading.Thread(
            target=self.mark_train_as_stopped, daemon=True
        )
        self.update_thread.start()
        print(f"[CONTROLLER: ENVIRONMENT] Initialised with {len(self.trains)} trains.")

    def update_train(self, index, gpsData: GPSData):
        self.trains[index].curr_segment = gpsData.segment
        self.trains[index].next_segment = gpsData.next_segment
        self.trains[index].speed = max(gpsData.speed, 0)
        self.trains[index].distance_remaining = max(gpsData.distanceRemaining, 0)
        self.trains[index].direction = gpsData.direction
        self.trains[index].last_updated = self.timer.elapsed_time
        self.isRunning[index] = True

    def mark_train_as_stopped(self):
        curr_time = self.timer.elapsed_time
        for i in range(len(self.trains)):
            if curr_time - self.trains[i].last_updated > 5:
                self.isRunning[i] = False
                self.trains[i].curr_segment = 7
                self.trains[i].next_segment = 7
                self.trains[i].speed = 0
                self.trains[i].distance_remaining = 0
                self.trains[i].direction = 0
                self.trains[i].last_updated = curr_time

    def get_observation(self, number) -> dict:
        observations = {}
        for i in range(min(len(self.trains), number)):
            train = self.trains[i]
            observations[f"train_{i}"] = {
                "segment": train.curr_segment,
                "next_segment": train.next_segment,
                "speed": np.array([max(train.speed, 0)], dtype=np.float32),
                "distance_remaining": np.array(
                    [max(train.distance_remaining, 0)], dtype=np.float32
                ),
                "direction": train.direction,
            }

        for i in range(len(self.trains), number):
            observations[f"train_{i}"] = {
                "segment": 7,
                "next_segment": 7,
                "speed": np.array([0], dtype=np.float32),
                "distance_remaining": np.array([0], dtype=np.float32),
                "direction": 0,
            }

        return observations

    def validate_path(self, curr_segment, next_segment, direction):
        possible_paths = self.adjacency_list[curr_segment]
        is_right_direction = [False] * len(possible_paths)
        for i in range(len(possible_paths)):
            if direction == 0:
                is_right_direction[i] = possible_paths[i] > curr_segment
            else:
                is_right_direction[i] = possible_paths[i] < curr_segment
        for i in range(len(possible_paths)):
            if possible_paths[i] == next_segment:
                return is_right_direction[i]
        return False

    def send_action(self, index, next_segment, next_halt_time):
        if not self.isRunning[index]:
            return
        data = Control(
            next_segment=next_segment, next_halt_time=next_halt_time
        ).model_dump_json()
        self.udp_socket.sendto(data.encode("utf-8"), self.multicast_groups[index])

    def process_action(
        self, action: dict, is_collision: bool, observation: dict, step_count
    ):
        action = list(action.values())
        observation = list(observation.values())
        action = action[: self.no_trains]
        observation = observation[: self.no_trains]

        reward = 10

        allInactive = True

        for i in range(self.no_trains):
            if self.isRunning[i]:
                allInactive = False
                break

        if allInactive:
            reward = min(reward, 0)

        if is_collision:
            reward = min(reward, -10)

        actions_are_valid = True

        for i in range(self.no_trains):
            curr_segment = observation[i]["segment"]
            next_segment = action[i]["next_segment"]
            direction = observation[i]["direction"]  # 0: along, 1: against
            if curr_segment != 7 and not self.validate_path(
                curr_segment, next_segment, direction
            ):
                reward = min(reward, 0)
                actions_are_valid = False
                break

        covered_segments = set()
        for i in range(len(action)):
            if action[i]["next_segment"] != 7 and observation[i]["segment"] != 7:
                if action[i]["next_segment"] in covered_segments:
                    reward = min(reward, 5)
                covered_segments.add(action[i]["next_segment"])

        if actions_are_valid:
            for i in range(len(action)):
                self.send_action(
                    i, action[i]["next_segment"], action[i]["next_halt_time"]
                )

        # print(
        #     f"Step {step_count}: {reward} for {[int(action[i]['next_segment']) for i in range(self.no_trains)]} and {[observation[i]['segment'] for i in range(self.no_trains)]}"
        # )

        return reward

    def destroy(self):
        self.udp_socket.close()
        self.update_thread.join()
        print("[CONTROLLER: ENVIRONMENT] Destroyed environment.")
