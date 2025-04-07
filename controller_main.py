from configObject import config
from controller.socket_listener import (
    start_tcp_server,
    start_udp_servers,
    stop_all_servers,
)
import time

if __name__ == "__main__":
    start_tcp_server()
    start_udp_servers(config.entities.trains)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all_servers()
        print("\nShutting down RailGuard controller...")
