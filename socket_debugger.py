import socket
import threading
import json

# Server configuration
TCP_HOST = "localhost"
TCP_PORT = 8080


def start_tcp_server():
    """Handles the TCP connection for receiving InitialData and sending 'READY'."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((TCP_HOST, TCP_PORT))
        server_socket.listen(5)
        print(f"[TCP] Listening on {TCP_HOST}:{TCP_PORT}...")

        try:
            while True:
                conn, addr = server_socket.accept()
                print(f"\n[TCP] [+] Connection established from {addr}")

                with conn:
                    while True:
                        try:
                            data = conn.recv(4096)
                            if not data:
                                print(f"[TCP] [-] Connection closed by {addr}")
                                break

                            decoded_data = data.decode("utf-8").strip()
                            print("\n==============================")
                            print(f"[TCP] [Received from {addr}]")
                            print(decoded_data)
                            print("==============================\n")

                            # Parse JSON data to get the number of trains
                            try:
                                json_data = json.loads(decoded_data)
                                train_count = json_data.get("trains", 0)
                                print(f"[TCP] [+] Number of trains: {train_count}")

                                conn.sendall(b"READY")
                                print("[TCP] [+] Sent 'READY' to sender.")

                                # Start UDP servers dynamically based on train_count
                                start_udp_servers(train_count)

                            except json.JSONDecodeError as e:
                                print(f"[TCP] [!] JSON decode error: {e}")

                        except Exception as e:
                            print(f"[TCP] [!] Error while receiving data: {e}")
                            break

        except KeyboardInterrupt:
            print("\n[TCP] [!] Server stopped manually.")


def start_udp_server(udp_port):
    """Handles the UDP connection for continuously receiving TrainCoords data."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((TCP_HOST, udp_port))
        print(f"[UDP] Listening on {TCP_HOST}:{udp_port}...\n")

        try:
            while True:
                data, addr = udp_socket.recvfrom(4096)
                decoded_data = data.decode("utf-8").strip()
                print("\n==============================")
                print(f"[UDP Port {udp_port}] [Received from {addr}]")
                print(decoded_data)
                print("==============================\n")

        except KeyboardInterrupt:
            print(f"\n[UDP Port {udp_port}] [!] Server stopped manually.")


def start_udp_servers(train_count):
    """Starts multiple UDP servers dynamically based on the number of trains."""
    udp_threads = []
    for i in range(train_count):
        udp_port = 8081 + i
        udp_thread = threading.Thread(
            target=start_udp_server, args=(udp_port,), daemon=True
        )
        udp_threads.append(udp_thread)
        udp_thread.start()
        print(f"[Main] [+] Started UDP server on port {udp_port}")

    # Let all threads run in the background
    for t in udp_threads:
        t.join()


if __name__ == "__main__":
    tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
    tcp_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Main] [!] Stopping all servers...")
