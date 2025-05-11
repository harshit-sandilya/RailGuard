import json
import socket
import struct
import threading

from pydantic import ValidationError

from schema import GPSData


class TrainListeners:
    udp_threads = []
    isRunning = []

    def __init__(self, environment, train_count, base_port):
        self.environment = environment
        self.train_count = train_count
        self.environment.initialise_trains(train_count)
        self.isRunning = [False] * train_count
        self.base_port = base_port

    def start(self):
        for i in range(self.train_count):
            udp_port = self.base_port + i
            udp_thread = threading.Thread(
                target=self.start_udp_server,
                args=(
                    i,
                    udp_port,
                ),
                daemon=True,
            )
            self.udp_threads.append(udp_thread)
            udp_thread.start()
            self.isRunning[i] = True
        print(f"[CONTROLLER: TRAIN LISTENERS] Started {self.train_count} UDP servers.")

    def stop(self):
        for i in range(self.train_count):
            self.isRunning[i] = False
            self.udp_threads[i].join()
            print(
                f"[CONTROLLER: TRAIN LISTENERS: UDP] Stopped UDP server on port {self.base_port + i}"
            )
        print("[CONTROLLER: TRAIN LISTENERS] All UDP servers stopped.")

    def start_udp_server(self, index, udp_port):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            print(
                "[CONTROLLER: TRAIN LISTENERS: UDP] SO_REUSEPORT not supported on this platform"
            )
        udp_socket.bind(("0.0.0.0", udp_port))
        udp_socket.settimeout(1)

        multicast_group = "224.0.0.1"
        group = socket.inet_aton(multicast_group)
        mreq = struct.pack("4sL", group, socket.INADDR_ANY)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(
            f"[CONTROLLER: TRAIN LISTENERS: UDP] Listening on {multicast_group}:{udp_port}..."
        )
        while self.isRunning[index]:
            try:
                data, addr = udp_socket.recvfrom(4096)
                decoded_data = data.decode("utf-8").strip()
                json_data = json.loads(decoded_data)
                gpsData = GPSData(**json_data)
                self.environment.update_train(udp_port - self.base_port, gpsData)

            except socket.timeout:
                continue
            except json.JSONDecodeError:
                print(
                    f"[CONTROLLER: TRAIN LISTENERS: UDP Port {udp_port}] [!] JSON decode error"
                )
            except ValidationError:
                continue
            except Exception:
                print(
                    f"[CONTROLLER: TRAIN LISTENERS: UDP Port {udp_port}] [!] Error while receiving data"
                )
        udp_socket.close()
