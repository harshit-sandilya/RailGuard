import os
import time
import threading


class LogWatcher:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.open_file()
        self.last_position = 0
        print("[Log Watcher] Log file opened.")

    def open_file(self):
        while not os.path.exists(self.log_file_path):
            print("[Log Watcher] Waiting for log file to appear...")
            time.sleep(0.5)
        self.file = open(self.log_file_path, "r")

    def get_collisions(self):
        collision_marker = "=== COLLISION DETECTED ==="
        collision_count = 0
        current_position = self.file.tell()

        try:
            self.file.seek(0)
            for line in self.file:
                if collision_marker in line:
                    collision_count += 1

            print(
                f"[Log Watcher] Found {collision_count} collision(s) in the log file."
            )
            return collision_count

        finally:
            self.file.seek(current_position)

    def watch_blocking(self, marker):
        print(f"[Log Watcher] Watching for marker: '{marker}'")
        found_marker = False
        found_lock = threading.Lock()
        found_event = threading.Event()

        def backward_search():
            nonlocal found_marker
            current_position = self.last_position
            self.file.seek(0)
            backward_lines = self.file.readlines()

            # Reverse the lines to search from current_position to 0
            for line in reversed(backward_lines):
                if marker in line:
                    with found_lock:
                        if not found_marker:
                            print(
                                f"[Log Watcher] Found (backward): '{marker}' in line: {line.strip()}"
                            )
                            found_marker = True
                            found_event.set()
                            return True

            return False

        backward_thread = threading.Thread(target=backward_search)
        backward_thread.daemon = True
        backward_thread.start()

        while not found_marker and not found_event.is_set():
            self.file.seek(self.last_position)
            new_lines = self.file.readlines()
            self.last_position = self.file.tell()

            for line in new_lines:
                if marker in line:
                    with found_lock:
                        print(
                            f"[Log Watcher] Found (forward): '{marker}' in line: {line.strip()}"
                        )
                        found_marker = True
                        found_event.set()
                        break

            if found_marker:
                break

            if not new_lines:
                time.sleep(0.1)

        # Wait for the backward thread to complete
        backward_thread.join(timeout=1.0)

        return found_marker
