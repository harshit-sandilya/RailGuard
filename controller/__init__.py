from .Environment import Environment
from .train_listeners import TrainListeners
from .update_channel import UpdateChannel


class Controller:
    def __init__(self, environment: Environment, train_count: int, port: int):
        self.updates = UpdateChannel(environment, port)
        self.listeners = TrainListeners(environment, train_count, port + 1)
        self.environment = environment

    def start(self):
        self.updates.start()
        self.listeners.start()

    def stop(self):
        self.updates.stop()
        self.listeners.stop()


__all__ = ["Controller", "Environment"]
