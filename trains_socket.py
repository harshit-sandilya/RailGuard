import socket
import threading
import time

from schema import TrainCoords
from schema.timer import TimerFormat
from timer import TIME_SECOND, ResettableTimer
from train_position_getter import get_coords_of_trains

TIMER = ResettableTimer(max_time=(5 * 60 * 60 - 1))


class TrainSocket(threading.Thread):
    def __init__(self, train, host="127.0.0.1", port=8081):
        super().__init__()
        self.train = train
        self.host = host
        self.port = port
        self.running = True
        self.from_index = 0
        self.to_index = 1

        schedules = train["schedules"]
        smallest_day = schedules[0]["arrival_day"]
        smallest_time = schedules[0]["arrival"]
        largest_day = schedules[-1]["departure_day"]
        largest_time = schedules[-1]["departure"]

        self.smallest = TimerFormat(
            day=smallest_day,
            hours=smallest_time.split(":")[0],
            minutes=smallest_time.split(":")[1],
            seconds=smallest_time.split(":")[2],
        )
        self.largest = TimerFormat(
            day=largest_day,
            hours=largest_time.split(":")[0],
            minutes=largest_time.split(":")[1],
            seconds=largest_time.split(":")[2],
        )

        print(f"Train: {train['train_no']} connects to {host} and port {port}")

    def send_update(self, client_socket, train_coords: TrainCoords):
        data = train_coords.model_dump_json()

        try:
            client_socket.sendto(data.encode("utf-8"), (self.host, self.port))
            print(f"Sent: Train {self.train['train_no']} at {train_coords}")
        except socket.error as e:
            print(f"[ERROR] Could not send data: {e}")
            time.sleep(TIME_SECOND / 4)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            print(f"Train {self.train['train_no']} socket ready.")

            while self.running:
                current_time = TIMER.get_time()
                train_coords = get_coords_of_trains(
                    current_time,
                    self.train,
                    self.from_index,
                    self.to_index,
                    self.smallest,
                    self.largest,
                )

                if train_coords:
                    self.send_update(client_socket, train_coords)

                time.sleep(TIME_SECOND)

            print(f"Train {self.train['train_no']} disconnected")

    def stop(self):
        self.running = False
