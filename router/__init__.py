import json
import threading
import time

from .train_senders import TrainSender
from .update_channel import UpdateChannel


class Router:
    sockets = []

    def __init__(
        self,
        base_dir,
        port,
        global_timer,
        train_length,
        station_width,
        seconds_per_tick,
    ):
        self.base_dir = base_dir
        self.port = port
        self.global_timer = global_timer
        with open(f"{self.base_dir}/trains.json", "r") as file:
            train_data = json.load(file)
        self.update_channel = UpdateChannel(
            base_dir=self.base_dir,
            train_data=train_data,
            port=self.port,
            global_timer=self.global_timer,
            train_length=train_length,
            station_width=station_width,
        )
        self.trains_are_done = [False] * len(train_data)
        self.train_senders = [
            TrainSender(
                train,
                port + index + 1,
                global_timer,
                seconds_per_tick,
                self.trains_are_done,
                index,
            )
            for index, train in enumerate(train_data)
        ]
        self.finish_checker_thread = None
        self.is_running = False

    def _check_trains_done(self):
        while self.is_running:
            if all(self.trains_are_done) and any(self.trains_are_done):
                print("[ROUTER] All trains completed. Sending finish signal...")
                self.update_channel.send_finish_signal()
                break
            time.sleep(0.5)

    def start(self):
        print("[ROUTER] Starting the router...")
        self.is_running = True
        self.update_channel.start()
        for sender in self.train_senders:
            sender.start()
        self.finish_checker_thread = threading.Thread(target=self._check_trains_done)
        self.finish_checker_thread.daemon = True
        self.finish_checker_thread.start()

    def stop(self):
        self.is_running = False
        self.update_channel.stop()
        for sender in self.train_senders:
            sender.stop()
        if self.finish_checker_thread and self.finish_checker_thread.is_alive():
            self.finish_checker_thread.join(timeout=1.0)
        print("[ROUTER] Stopped the router")
