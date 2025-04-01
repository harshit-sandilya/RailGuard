import json
import socket
import time

from configObject import TIME_SECOND, TIMER, BASE_DIR
from get_initial_data import get_initial_data
from trains_socket import TIMER, TrainSocket

HOST = "127.0.0.1"
PORT = 8080


def send_initial_data(train_data, BASE_DIR):
    """Sends the InitialData to Unity and waits until Unity is ready."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        client_socket.settimeout(5)
        initial_data = get_initial_data(train_data, BASE_DIR=BASE_DIR)
        initial_data = initial_data.model_dump_json()
        multicast_group = ("224.0.0.1", PORT)
        print("Sending InitialData to Unity...")
        client_socket.sendto(initial_data.encode("utf-8"), multicast_group)
        print("Sent InitialData to Unity. Waiting for Unity to get ready...")

        while True:
            try:
                response, _ = client_socket.recvfrom(1024)
                response = response.decode("utf-8").strip()
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
    if send_initial_data(train_data, BASE_DIR):
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
