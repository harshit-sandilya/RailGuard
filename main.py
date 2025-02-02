import socket
import pickle
import time
from train_position_getter import train_numbers
from get_initial_data import get_initial_data
from trains_socket import TrainSocket, TIMER

HOST = "127.0.0.1"
PORT = 5000

def send_initial_data():
    """Sends the InitialData to Unity and waits until Unity is ready."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        initial_data = get_initial_data()
        data = pickle.dumps(initial_data)
        client_socket.sendall(data)
        print("Sent InitialData to Unity. Waiting for Unity to get ready...")

        while True:
            try:
                response = client_socket.recv(1024).decode()
                if response == "READY":
                    print("Unity is ready. Starting train data transmission.")
                    return True
            except socket.timeout:
                continue

if __name__ == "__main__":
    send_initial_data()
    TIMER.start()
    sockets = [TrainSocket(train_no) for train_no in train_numbers]

    for sock in sockets:
        sock.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping all train sockets...")
        for sock in sockets:
            sock.stop()
            TIMER.stop()
            TIMER.join()
