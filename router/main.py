import json

from kafka import KafkaProducer
from schema import Config, InitData
from utils import read_config

from .get_stations import get_stations
from .get_tracks import get_tracks

config: Config = read_config()

topic = "route"
producer = KafkaProducer(
    bootstrap_servers=f"{config.server.host}:{config.server.kafka_port}",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def send_init_data(track_points):
    """Sends the InitData to Unity"""
    stations = get_stations(config.data_dir)
    tracks = get_tracks(
        stations, track_points, config.train.length / 1000, config.station.width / 1000
    )
    data = InitData(stations=stations, tracks=tracks)
    print("====================================")
    print(json.dumps(data, indent=4, default=lambda o: o.__dict__))
    print("====================================")
    producer.send(topic, value=json.dumps(data, default=lambda o: o.__dict__))
    producer.flush()
    # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
    #     client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    #     client_socket.settimeout(5)
    #     initial_data = get_initial_data(no_trains=no_trains, BASE_DIR=BASE_DIR)
    #     initial_data = initial_data.model_dump_json()
    #     multicast_group = ('224.0.0.1', PORT)
    #     print("Sending InitialData to Unity...")
    #     client_socket.sendto(initial_data.encode("utf-8"), multicast_group)
    #     print("Sent InitialData to Unity. Waiting for Unity to get ready...")

    #     while True:
    #         try:
    #             response, _ = client_socket.recvfrom(1024)
    #             response = response.decode("utf-8").strip()
    #             if response == "READY":
    #                 print("Unity is ready. Starting train data transmission.")
    #                 return True
    #         except socket.timeout:
    #             print("Waiting for Unity to respond...")
    #             continue
    #         except Exception as e:
    #             print(f"Error while receiving data: {e}")
    #             break

    #     return False


def main():
    with open(f"{config.data_dir}/trains.json", "r") as file:
        train_data = json.load(file)
    track_points = [train_data[i]["coordinates"] for i in range(len(train_data))]
    send_init_data(track_points)
    # Starting train routers


if __name__ == "__main__":
    main()
