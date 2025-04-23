import os
import time


def wait_for_unity_playmode(log_path, markers=None):
    if markers is None:
        markers = [
            "== UNITY_PLAYMODE_START ==",
            "Server started, waiting for Python connection...",
        ]

    print(f"[log-watcher] Waiting for log markers: {markers}")

    found = {marker: False for marker in markers}

    while not os.path.exists(log_path):
        print("[log-watcher] Waiting for log file to appear...")
        time.sleep(0.5)

    with open(log_path, "r") as log_file:
        log_file.seek(0, os.SEEK_END)

        while not all(found.values()):
            line = log_file.readline()
            if not line:
                time.sleep(0.5)
                continue

            for marker in markers:
                if marker in line and not found[marker]:
                    print(f"[log-watcher] Found: '{marker}'")
                    found[marker] = True
