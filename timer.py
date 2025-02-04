import threading
import time

from schema.timer import TimerFormat

TIME_SECOND = 1/20

class ResettableTimer(threading.Thread):
    def __init__(self, max_time):
        super().__init__()
        self.max_time = max_time
        self.elapsed_time = 0
        self.days = 0
        self.running = False
        self.lock = threading.Lock()

    def get_human_format(self):
        return TimerFormat(
            day=self.days,
            hours=self.elapsed_time // 3600,
            minutes=(self.elapsed_time % 3600) // 60,
            seconds=self.elapsed_time % 60,
        )

    def run(self):
        """Function that runs in the thread to keep track of time."""
        self.running = True
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
