from configObject import config
from controller.socket_listener import start_tcp_server, start_udp_servers

if __name__ == "__main__":
    start_tcp_server()
    start_udp_servers(config.entities.trains)
