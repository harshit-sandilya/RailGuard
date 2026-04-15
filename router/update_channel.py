import socket
import threading

from utils import get_initial_data


class UpdateChannel:
    isRunning = False

    def __init__(
        self, base_dir, train_data, port: int, global_timer, train_length, station_width
    ):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.server_socket.settimeout(5)
        self.initial_data = get_initial_data(
            train_data, base_dir, train_length, station_width
        )
        self.initial_data = self.initial_data.model_dump_json()
        self.multicast_group = ("224.0.0.1", port)
        self.global_timer = global_timer

    def start(self):
        print("[ROUTER: UPDATE] Sending InitialData to Unity...")
        self.server_socket.sendto(
            self.initial_data.encode("utf-8"), self.multicast_group
        )
        print(
            "[ROUTER: UPDATE] Sent InitialData to Unity. Waiting for Unity to get ready..."
        )
        isReady = False
        while not isReady:
            try:
                response, _ = self.server_socket.recvfrom(1024)
                response = response.decode("utf-8").strip()
                if response == "READY":
                    print("[ROUTER: UPDATE] Unity is ready.")
                    isReady = True
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ROUTER: UPDATE] Error while receiving data: {e}")
                break
        self.isRunning = True
        self.global_timer.start()
        self.thread = threading.Thread(target=self.run_channel)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.isRunning = False
        self.thread.join()
        self.server_socket.close()
        print("[ROUTER: UPDATE] Stopped the UpdateChannel.")

    def run_channel(self):
        while self.isRunning:
            try:
                response, _ = self.server_socket.recvfrom(1024)
                response = response.decode("utf-8").strip()
                print(f"[ROUTER: UPDATE] Received data: {response}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ROUTER: UPDATE] Error while receiving data: {e}")
                break

    def send_finish_signal(self):
        finish_signal = "== ROUTER FINISH =="
        self.server_socket.sendto(finish_signal.encode("utf-8"), self.multicast_group)
        print("[ROUTER: UPDATE] Sent finish signal to Unity.")
