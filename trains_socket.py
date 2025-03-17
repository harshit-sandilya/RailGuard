import socket
import threading
import time

from constants import DAY_HOURS, TIME_SECOND
from schema import TrainData
from schema.timer import TimerFormat
from timer import ResettableTimer
from utils import str_to_timer, timer_to_seconds

TIMER = ResettableTimer(max_time=(DAY_HOURS * 60 * 60 - 1))


class TrainSocket(threading.Thread):
    def __init__(self, train, host="127.0.0.1", port=8081):
        super().__init__()
        self.train = train
        self.host = host
        self.port = port
        self.running = True
        self.from_index = 0
        self.to_index = 1
        self.trips = 0

        schedules = train["schedules"]
        smallest_day = schedules[0]["arrival_day"]
        smallest_time = schedules[0]["arrival"]
        largest_day = schedules[-1]["departure_day"]
        largest_time = schedules[-1]["departure"]

        self.smallest = str_to_timer(smallest_day, smallest_time)
        self.largest = str_to_timer(largest_day, largest_time)

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.multicast_group = ("224.0.0.1", port)

        print(f"Train {train['train_no']} initialized.")

    def send_update(self, train_data: TrainData):
        data = train_data.model_dump_json()

        try:
            self.udp_socket.sendto(data.encode("utf-8"), self.multicast_group)
            print(f"Sent: Train {self.train['train_no']} at {train_data}")
        except socket.error as e:
            print(f"[ERROR] Could not send data: {e}")

    def get_next_segment(self, curr_time:TimerFormat):
        from_time = str_to_timer(
            self.train["schedules"][self.from_index]["departure_day"],
            self.train["schedules"][self.from_index]["departure"],
        )
        to_time = str_to_timer(
            self.train["schedules"][self.to_index]["arrival_day"],
            self.train["schedules"][self.to_index]["arrival"],
        )
        next_dep = str_to_timer(
            self.train["schedules"][self.to_index]["departure_day"],
            self.train["schedules"][self.to_index]["departure"],
        )
        if curr_time < from_time:
            return None
        data = TrainData(
            number=self.train["train_no"],
            start_coords=self.train["coordinates"][self.from_index],
            end_coords=self.train["coordinates"][self.to_index],
            time_allocated=timer_to_seconds(to_time - from_time),
            halt_time=timer_to_seconds(next_dep - to_time),
        )
        return data

    def run(self):
        print(f"Train {self.train['train_no']} thread started.")

        while self.running:
            current_time = TIMER.get_time()
            while current_time < self.smallest:
                time.sleep(TIME_SECOND)
                current_time = TIMER.get_time()
            while current_time < self.largest:
                data = self.get_next_segment(current_time)
                if data is not None:
                    self.send_update(data)
                    self.from_index = self.to_index
                    self.to_index = self.to_index + 1 if self.to_index < len(self.train["schedules"]) - 1 else 0
                time.sleep(TIME_SECOND)
                current_time = TIMER.get_time()
            self.trips += 1
            self.smallest.day = self.smallest.day + self.largest.day
            self.largest.day += self.largest.day

        print(f"Train {self.train['train_no']} thread stopped.")

    def stop(self):
        self.running = False
        self.udp_socket.close()
