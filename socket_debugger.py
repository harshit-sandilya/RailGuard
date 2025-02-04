import socket

HOST = "localhost"  # Change if needed
PORT = 8080         # Set to the port your Unity/Python script is using

def start_debugger():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)  # Allow up to 5 connections
        print(f"Debugger listening on {HOST}:{PORT}...")

        try:
            while True:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Connected by {addr}")

                    while True:
                        data = conn.recv(4096)
                        if not data:
                            break

                        print("\n=================")
                        print("Received Data:\n", data.decode('utf-8'))
                        print("=================\n")

        except KeyboardInterrupt:
            print("\nDebugger stopped manually. Exiting...")

if __name__ == "__main__":
    start_debugger()
