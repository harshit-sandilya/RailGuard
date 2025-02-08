import socket
import threading

# Server configuration
TCP_HOST = "localhost"
TCP_PORT = 8080
UDP_PORT = 8081


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

                            conn.sendall(b"READY")
                            print("[TCP] [+] Sent 'READY' to sender.")

                        except Exception as e:
                            print(f"[TCP] [!] Error while receiving data: {e}")
                            break

        except KeyboardInterrupt:
            print("\n[TCP] [!] Server stopped manually.")


def start_udp_server():
    """Handles the UDP connection for continuously receiving TrainCoords data."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((TCP_HOST, UDP_PORT))
        print(f"[UDP] Listening on {TCP_HOST}:{UDP_PORT}...\n")

        try:
            while True:
                data, addr = udp_socket.recvfrom(4096)
                decoded_data = data.decode("utf-8").strip()
                print("\n==============================")
                print(f"[UDP] [Received from {addr}]")
                print(decoded_data)
                print("==============================\n")

        except KeyboardInterrupt:
            print("\n[UDP] [!] Server stopped manually.")


if __name__ == "__main__":
    tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
    udp_thread = threading.Thread(target=start_udp_server, daemon=True)

    tcp_thread.start()
    udp_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Main] [!] Stopping both servers...")
