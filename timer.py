import threading
import time
import socket
import json
from datetime import datetime

from constants import TIME_SECOND
from schema.timer import TimerFormat


class ResettableTimer(threading.Thread):
    def __init__(self, max_time):
        super().__init__()
        self.max_time = max_time
        self.elapsed_time = 0
        self.days = 0
        self.running = False
        self.lock = threading.Lock()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_port = 8079
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(("localhost", self.udp_port))
        self.udp_socket.settimeout(1)
        self.udp_thread = threading.Thread(target=self.get_time_over_udp, daemon=True)

    def get_human_format(self):
        return TimerFormat(
            day=self.days,
            hours=self.elapsed_time // 3600,
            minutes=(self.elapsed_time % 3600) // 60,
            seconds=self.elapsed_time % 60,
        )

    def get_time_over_udp(self):
        """Receives time updates over UDP and synchronizes elapsed time."""
        while self.running:
            try:
                data, _ = self.udp_socket.recvfrom(1024)
                message = data.decode()
                timer_data = json.loads(message)

                system_time = timer_data["system_time"]
                elapsed_time_received = timer_data["elapsed_time"]

                system_time_now = datetime.utcnow()
                received_seconds = system_time[0] * 3600 + system_time[1] * 60 + system_time[2] + system_time[3] / 1000
                current_seconds = system_time_now.hour * 3600 + system_time_now.minute * 60 + system_time_now.second + round(system_time_now.microsecond / 1000000,3)
                time_diff = current_seconds - received_seconds
                adjusted_elapsed_time = int(elapsed_time_received + time_diff / TIME_SECOND)

                with self.lock:
                    elapsed_diff = abs(adjusted_elapsed_time - self.elapsed_time)
                    if elapsed_diff > 5:
                        self.elapsed_time = adjusted_elapsed_time
                        print(f"Timer synchronized: Elapsed={self.elapsed_time}, System Time={system_time}")

            except Exception as e:
                print(f"Error receiving UDP data: {e}")


    def run(self):
        """Function that runs in the thread to keep track of time."""
        self.running = True
        self.udp_thread.start()
        while self.running:
            time.sleep(TIME_SECOND)
            with self.lock:
                self.elapsed_time += 1
                print(f"Time passed: {self.get_human_format()}")
                if self.elapsed_time >= self.max_time:
                    print("Timer reset!")
                    self.days += 1
                    self.elapsed_time = 0

    def stop(self):
        """Stops the timer thread."""
        self.running = False
        self.udp_thread.join()
        self.udp_socket.close()

    def reset(self):
        """Manually reset the timer."""
        with self.lock:
            self.elapsed_time = 0
            print("Timer manually reset!")

    def get_time(self):
        """Returns the current elapsed time."""
        with self.lock:
            return self.get_human_format()


if __name__ == "__main__":
    timer = ResettableTimer(max_time=(5 * 60 * 60 - 1))
    timer.start()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping timer...")
        timer.stop()
        timer.join()
