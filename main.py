import socket
import time
# import json
from train_position_getter import train_numbers
from get_initial_data import get_initial_data
from trains_socket import TrainSocket, TIMER
from timer import TIME_SECOND

HOST = "127.0.0.1"
PORT = 8080

def send_initial_data():
    """Sends the InitialData to Unity and waits until Unity is ready."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        initial_data = get_initial_data()
        initial_data = initial_data.model_dump_json()
        print("Sending InitialData to Unity...")
        client_socket.sendall(initial_data.encode('utf-8'))
        print("Sent InitialData to Unity. Waiting for Unity to get ready...")
        client_socket.settimeout(5)

        while True:
            try:
                response = client_socket.recv(1024).decode('utf-8')
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
    if send_initial_data():
        TIMER.start()
        sockets = [TrainSocket(train_no) for train_no in train_numbers]

        for sock in sockets:
            sock.run()

        try:
            while True:
                time.sleep(TIME_SECOND)
        except KeyboardInterrupt:
            print("Stopping all train sockets...")
            for sock in sockets:
                sock.stop()

            TIMER.stop()
            TIMER.join()

if __name__ == "__main__":
    main()
