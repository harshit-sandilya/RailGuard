import pickle
import socket
import threading
import time

from timer import ResettableTimer
from train_position_getter import get_coords_of_trains

TIMER = ResettableTimer(max_time=(5 * 60 * 60 - 1))

class TrainSocket(threading.Thread):
    def __init__(self, train_no, host="127.0.0.1", port=5000):
        super().__init__()
        self.train_no = train_no
        self.host = host
        self.port = port
        self.running = True

    def send_update(self, client_socket, train_coords):
        data = pickle.dumps(train_coords)
        client_socket.sendall(data)
        print(f"Sent: Train {self.train_no} at {train_coords}")

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            print(f"Train {self.train_no} socket connected.")

            while self.running:
                current_time = TIMER.get_time()
                train_coords = get_coords_of_trains(current_time, self.train_no)

                if train_coords:
                    self.send_update(client_socket, train_coords)

                time.sleep(1)

    def stop(self):
        self.running = False
