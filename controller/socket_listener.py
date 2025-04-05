import socket
import struct
import threading
import json
from schema import InitialData
from .globals import environment

TCP_HOST = "0.0.0.0"
TCP_PORT = 8080
isRunning = True
udp_threads = []


def start_tcp_server():
    """Handles the UDP connection for receiving InitialData"""
    global isRunning
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        print("[UDP] SO_REUSEPORT not supported on this platform")

    server_socket.bind((TCP_HOST, TCP_PORT))
    server_socket.settimeout(5)

    multicast_group = "224.0.0.1"
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack("4sL", group, socket.INADDR_ANY)
    server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f"[UDP] Listening on {multicast_group}:{TCP_PORT}...")

    while isRunning:
        try:
            data, addr = server_socket.recvfrom(4096)
            print(f"\n[UDP] [+] Data received from {addr}")

            decoded_data = data.decode("utf-8").strip()
            print("\n==============================")
            print(f"[UDP] [Received from {addr}]")
            print(decoded_data)
            print("==============================\n")

            try:
                json_data = json.loads(decoded_data)
                initData = InitialData(**json_data)
                environment.initialise(initData)
                print(f"[UDP] [+] InitialData object created: {initData}")
                break

            except json.JSONDecodeError as e:
                print(f"[UDP] [!] JSON decode error: {e}")

        except socket.timeout:
            continue
        except Exception as e:
            print(f"[UDP] [!] Error while receiving data: {e}")
    server_socket.close()


def start_udp_server(udp_port):
    """Handles the UDP connection for continuously receiving GPS data."""
    global isRunning
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        print("[UDP] SO_REUSEPORT not supported on this platform")
    udp_socket.bind((TCP_HOST, udp_port))
    udp_socket.settimeout(1)

    multicast_group = "224.0.0.1"
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack("4sL", group, socket.INADDR_ANY)
    udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f"[UDP] Listening on {multicast_group}:{udp_port}...")

    while isRunning:
        try:
            data, addr = udp_socket.recvfrom(4096)
            decoded_data = data.decode("utf-8").strip()
            print("\n==============================")
            print(f"[UDP Port {udp_port}] [Received from {addr}]")
            print(decoded_data)
            print("==============================\n")
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[UDP Port {udp_port}] [!] Error while receiving data: {e}")

    udp_socket.close()


def start_udp_servers(train_count):
    """Starts multiple UDP servers dynamically based on the number of trains."""
    for i in range(train_count):
        udp_port = 8081 + i
        udp_thread = threading.Thread(
            target=start_udp_server, args=(udp_port,), daemon=True
        )
        udp_threads.append(udp_thread)
        udp_thread.start()
        print(f"[Main] [+] Started UDP server on port {udp_port}")


def stop_all_servers():
    """Stops all servers gracefully."""
    global isRunning
    isRunning = False
    for thread in udp_threads:
        thread.join()
    print("[Main] [+] All servers stopped.")


# if __name__ == "__main__":
#     tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
#     tcp_thread.start()

#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         print("\n[Main] [!] Stopping all servers...")
#         isRunning = False
#         for thread in udp_threads:
#             thread.join()
#         tcp_thread.join()
#         print("[Main] [+] All servers stopped.")
