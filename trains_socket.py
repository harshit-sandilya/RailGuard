import socket
import threading
import time

from schema import TrainData
from schema.timer import TimerFormat
from utils import str_to_timer, timer_to_seconds
from configObject import TIME_SECOND
from timer_global import TIMER


class TrainSocket(threading.Thread):
    def __init__(self, train, host="127.0.0.1", port=8081):
        super().__init__()
        self.train = train
        self.host = host
        self.port = port
        self.running = True
        self.curr_segment = 0
        self.trips = 0
        self.TIME_SECOND = TIME_SECOND

        # schedules = train["schedules"]
        # smallest_day = schedules[0]["arrival_day"]
        # smallest_time = schedules[0]["arrival"]
        # largest_day = schedules[-1]["departure_day"]
        # largest_time = schedules[-1]["departure"]

        self.smallest = str_to_timer(0, train["start_time"])
        self.largest = str_to_timer(0, train["end_time"])

        self.get_segments()

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.multicast_group = ("224.0.0.1", port)

        print(
            f"Train {train['train_no']} initialized with {len(self.segments)} segments to cover."
        )

    def get_segments(self):
        self.segments = []
        assert (
            len(self.train["schedules"]) <= len(self.train["coordinates"])
            and len(self.train["schedules"]) >= len(self.train["coordinates"]) - 2
        )
        if len(self.train["schedules"]) == len(self.train["coordinates"]):
            for i in range(len(self.train["schedules"]) - 1):
                dept_time = str_to_timer(
                    self.train["schedules"][i]["departure_day"],
                    self.train["schedules"][i]["departure"],
                )
                arr_time = str_to_timer(
                    self.train["schedules"][i + 1]["arrival_day"],
                    self.train["schedules"][i + 1]["arrival"],
                )
                next_dep_time = str_to_timer(
                    self.train["schedules"][i + 1]["departure_day"],
                    self.train["schedules"][i + 1]["departure"],
                )
                start_coords = self.train["coordinates"][i]
                end_coords = self.train["coordinates"][i + 1]
                time_allocated = timer_to_seconds(arr_time - dept_time)
                halt_time = timer_to_seconds(next_dep_time - arr_time)
                self.segments.append(
                    [
                        TrainData(
                            number=self.train["train_no"],
                            start_coords=start_coords,
                            end_coords=end_coords,
                            time_allocated=time_allocated,
                            halt_time=halt_time,
                        ),
                        dept_time,
                    ]
                )
        elif len(self.train["schedules"]) == len(self.train["coordinates"]) - 2:
            self.segments.append(
                [
                    TrainData(
                        number=self.train["train_no"],
                        start_coords=self.train["coordinates"][0],
                        end_coords=self.train["coordinates"][1],
                        time_allocated=timer_to_seconds(
                            str_to_timer(
                                self.train["schedules"][0]["arrival_day"],
                                self.train["schedules"][0]["arrival"],
                            )
                            - self.smallest
                        ),
                        halt_time=timer_to_seconds(
                            str_to_timer(
                                self.train["schedules"][0]["departure_day"],
                                self.train["schedules"][0]["departure"],
                            )
                            - str_to_timer(
                                self.train["schedules"][0]["arrival_day"],
                                self.train["schedules"][0]["arrival"],
                            )
                        ),
                    ),
                    self.smallest,
                ]
            )
            for i in range(len(self.train["schedules"]) - 1):
                dept_time = str_to_timer(
                    self.train["schedules"][i]["departure_day"],
                    self.train["schedules"][i]["departure"],
                )
                arr_time = str_to_timer(
                    self.train["schedules"][i + 1]["arrival_day"],
                    self.train["schedules"][i + 1]["arrival"],
                )
                next_dep_time = str_to_timer(
                    self.train["schedules"][i + 1]["departure_day"],
                    self.train["schedules"][i + 1]["departure"],
                )
                start_coords = self.train["coordinates"][i]
                end_coords = self.train["coordinates"][i + 1]
                time_allocated = timer_to_seconds(arr_time - dept_time)
                halt_time = timer_to_seconds(next_dep_time - arr_time)
                self.segments.append(
                    [
                        TrainData(
                            number=self.train["train_no"],
                            start_coords=start_coords,
                            end_coords=end_coords,
                            time_allocated=time_allocated,
                            halt_time=halt_time,
                        ),
                        dept_time,
                    ]
                )
            self.segments.append(
                [
                    TrainData(
                        number=self.train["train_no"],
                        start_coords=self.train["coordinates"][-2],
                        end_coords=self.train["coordinates"][-1],
                        time_allocated=timer_to_seconds(
                            self.largest
                            - str_to_timer(
                                self.train["schedules"][-1]["departure_day"],
                                self.train["schedules"][-1]["departure"],
                            )
                        ),
                        halt_time=0,
                    ),
                    str_to_timer(
                        self.train["schedules"][-1]["departure_day"],
                        self.train["schedules"][-1]["departure"],
                    ),
                ]
            )

    def send_update(self, train_data: TrainData):
        data = train_data.model_dump_json()

        try:
            self.udp_socket.sendto(data.encode("utf-8"), self.multicast_group)
            print(f"Sent: Train {self.train['train_no']} at {train_data}")
        except socket.error as e:
            print(f"[ERROR] Could not send data: {e}")

    # def get_next_segment(self, curr_time: TimerFormat):
    #     from_time = str_to_timer(
    #         self.train["schedules"][self.from_index]["departure_day"],
    #         self.train["schedules"][self.from_index]["departure"],
    #     )
    #     to_time = str_to_timer(
    #         self.train["schedules"][self.to_index]["arrival_day"],
    #         self.train["schedules"][self.to_index]["arrival"],
    #     )
    #     next_dep = str_to_timer(
    #         self.train["schedules"][self.to_index]["departure_day"],
    #         self.train["schedules"][self.to_index]["departure"],
    #     )
    #     if curr_time < from_time:
    #         return None
    #     data = TrainData(
    #         number=self.train["train_no"],
    #         start_coords=self.train["coordinates"][self.from_index],
    #         end_coords=self.train["coordinates"][self.to_index],
    #         time_allocated=timer_to_seconds(to_time - from_time),
    #         halt_time=timer_to_seconds(next_dep - to_time),
    #     )
    #     return data

    def run(self):
        print(f"Train {self.train['train_no']} thread started.")

        while self.running:
            current_time = TIMER.get_time()
            while current_time < self.smallest:
                time.sleep(self.TIME_SECOND)
                current_time = TIMER.get_time()
            while current_time < self.largest:
                if self.curr_segment >= len(self.segments):
                    break
                if current_time >= self.segments[self.curr_segment][1]:
                    self.send_update(self.segments[self.curr_segment][0])
                    self.curr_segment += 1
                # data = self.get_next_segment(current_time)
                # if data is not None:
                #     self.send_update(data)
                #     self.from_index = self.to_index
                #     self.to_index = (
                #         self.to_index + 1
                #         if self.to_index < len(self.train["schedules"]) - 1
                #         else 0
                #     )
                time.sleep(self.TIME_SECOND)
                current_time = TIMER.get_time()
            self.trips += 1
            self.smallest.day = self.smallest.day + self.largest.day
            self.largest.day += self.largest.day

        print(f"Train {self.train['train_no']} thread stopped.")

    def stop(self):
        self.running = False
        self.udp_socket.close()
