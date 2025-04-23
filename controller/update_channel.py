import json
import socket
import struct
import threading

from schema import InitialData


class UpdateChannel:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    isRunning = False
    thread = None

    def __init__(self, environment, port):
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.environment = environment
        self.port = port

        try:
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            print(
                "[CONTROLLER: UPDATE: UDP] SO_REUSEPORT not supported on this platform"
            )

        self.client_socket.bind(("0.0.0.0", port))
        self.client_socket.settimeout(5)

        multicast_group = "224.0.0.1"
        group = socket.inet_aton(multicast_group)
        mreq = struct.pack("4sL", group, socket.INADDR_ANY)
        self.client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"[CONTROLLER: UPDATE: UDP] Listening on {multicast_group}:{port}...")

    def start(self):
        self.isRunning = True
        print("[CONTROLLER: UPDATE: UDP] Server running in background thread")
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.isRunning = False
        self.client_socket.close()
        self.thread.join()
        self.thread = None
        print("[CONTROLLER: UPDATE: UDP] Server stopped")

    def run(self):
        while self.isRunning:
            try:
                data, addr = self.client_socket.recvfrom(4096)
                print(f"[CONTROLLER: UPDATE: UDP] [+] Data received from {addr}")
                decoded_data = data.decode("utf-8").strip()

                json_data = json.loads(decoded_data)
                initData = InitialData(**json_data)
                self.environment.initialise(initData)

            except json.JSONDecodeError as e:
                print(f"[CONTROLLER: UPDATE: UDP] [!] JSON decode error: {e}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[CONTROLLER: UPDATE: UDP] [!] Error while receiving data: {e}")
