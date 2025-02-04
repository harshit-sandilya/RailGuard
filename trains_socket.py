import socket
import threading
import time

from timer import ResettableTimer, TIME_SECOND
from train_position_getter import get_coords_of_trains
from schema import TrainCoords

TIMER = ResettableTimer(max_time=(5 * 60 * 60 - 1))

class TrainSocket(threading.Thread):
    def __init__(self, train_no, host="127.0.0.1", port=8081):
        super().__init__()
        self.train_no = train_no
        self.host = host
        self.port = port
        self.running = True
        print(f"Train: {train_no} connects to {host} and port {port}")

    def send_update(self, client_socket, train_coords:TrainCoords):
        data = train_coords.model_dump_json()
        client_socket.sendall(data.encode('utf-8'))
        print(f"Sent: Train {self.train_no} at {train_coords}")

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.connect((self.host, self.port))
            print(f"Train {self.train_no} socket connected.")

            while self.running:
                current_time = TIMER.get_time()
                train_coords = get_coords_of_trains(current_time, self.train_no)

                if train_coords:
                    self.send_update(client_socket, train_coords)

                time.sleep(TIME_SECOND)

    def stop(self):
        self.running = False
