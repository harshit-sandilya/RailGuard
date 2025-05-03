import socket
import threading
import time

from schema import TrainData
from utils import str_to_timer, timer_to_seconds


class TrainSender:
    running = True
    curr_segment = 0

    def __init__(self, train, port, timer, seconds, trains_are_done, index):
        self.trains_are_done = trains_are_done
        self.timer = timer
        self.second = seconds
        self.train = train
        self.port = port
        self.index = index
        self.smallest = str_to_timer(0, train["start_time"])
        self.largest = str_to_timer(0, train["end_time"])
        self.get_segments()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.multicast_group = ("224.0.0.1", port)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        print(f"[TRAIN SENDER] Stopped TrainSender for train {self.train['train_no']}")

    def print_segments(self):
        for segment in self.segments:
            print(
                f"Train {self.train['train_no']} Segment: {segment[0].model_dump_json()} at time {segment[1]}"
            )

    def get_segments(self):
        self.segments = []
        assert len(self.train["schedules"]) == len(self.train["coordinates"]) - 2

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
            next_arr_time = str_to_timer(
                self.train["schedules"][i + 1]["arrival_day"],
                self.train["schedules"][i + 1]["arrival"],
            )
            next_dep_time = str_to_timer(
                self.train["schedules"][i + 1]["departure_day"],
                self.train["schedules"][i + 1]["departure"],
            )
            start_coords = self.train["coordinates"][i + 1]
            end_coords = self.train["coordinates"][i + 2]
            time_allocated = timer_to_seconds(next_arr_time - dept_time)
            halt_time = timer_to_seconds(next_dep_time - next_arr_time)
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
            print(
                f"[ROUTER: TRAIN] Sent data: {data} for train {self.train['train_no']} on port {self.port}"
            )
        except socket.error as e:
            print(
                f"[ROUTER: TRAIN] [!] Could not send data for train {self.train['train_no']}"
            )
            print(e)

    def run(self):
        while self.running:
            current_time = self.timer.get_time()
            while current_time < self.smallest and self.running:
                time.sleep(self.second / 10)
                current_time = self.timer.get_time()
            while current_time < self.largest and self.running:
                if self.curr_segment >= len(self.segments):
                    break
                if current_time >= self.segments[self.curr_segment][1]:
                    self.send_update(self.segments[self.curr_segment][0])
                    self.curr_segment += 1
                time.sleep(self.second / 10)
                current_time = self.timer.get_time()
            self.trains_are_done[self.index] = True
        print(
            f"[TRAIN SENDER] Train {self.train['train_no']} has completed its journey."
        )
        self.udp_socket.close()
