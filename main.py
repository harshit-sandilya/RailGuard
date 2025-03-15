import json
import socket
import time

from constants import TIME_SECOND
from get_initial_data import get_initial_data
from trains_socket import TIMER, TrainSocket

HOST = "127.0.0.1"
PORT = 8080
BASE_DIR = "./sample_scenarios/3stations2trains1day"
# BASE_DIR = "./data/generated"

def send_initial_data(no_trains: int, BASE_DIR):
    """Sends the InitialData to Unity and waits until Unity is ready."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        initial_data = get_initial_data(no_trains=no_trains, BASE_DIR=BASE_DIR)
        initial_data = initial_data.model_dump_json()
        print("Sending InitialData to Unity...")
        client_socket.sendall(initial_data.encode("utf-8"))
        print("Sent InitialData to Unity. Waiting for Unity to get ready...")
        client_socket.settimeout(5)

        while True:
            try:
                response = client_socket.recv(1024).decode("utf-8")
                response = response.strip()
                if response == "READY":
                    print("Unity is ready. Starting train data transmission.")
                    return True
            except socket.timeout:
                print("Waiting for Unity to respond...")
                continue
            except Exception as e:
                print(f"Error while receiving data: {e}")
                break

        return False


def main():
    with open(f"{BASE_DIR}/trains.json", "r") as file:
        train_data = json.load(file)
    no_trains = len(train_data)
    if send_initial_data(no_trains, BASE_DIR):
        TIMER.start()
        sockets = [
            TrainSocket(train, port=PORT + i + 1) for i, train in enumerate(train_data)
        ]

        for sock in sockets:
            sock.start()

        try:
            while True:
                time.sleep(TIME_SECOND)
        except KeyboardInterrupt:
            print("Stopping all train sockets...")
            for sock in sockets:
                sock.stop()

            for sock in sockets:
                sock.join()

            TIMER.stop()
            TIMER.join()


if __name__ == "__main__":
    main()
