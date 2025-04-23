import argparse
from System import System
from LogWatcher import LogWatcher
import os
import time

parser = argparse.ArgumentParser(
    description="Run the RailGuard system as a whole for a scenario"
)
parser.add_argument("--trains", type=int, help="Number of trains", required=True)
parser.add_argument("--stations", type=int, help="Number of stations", required=True)
parser.add_argument(
    "--simulate",
    action="store_true",
    default=False,
    help="Enable simulation mode without controller",
)
parser.add_argument(
    "--dev",
    action="store_true",
    default=False,
    help="Enable development mode with UI",
)
parser.add_argument("--port", type=int, default=8080, help="Starting port number")

args = parser.parse_args()
log_file_path = "logs/unity_log.txt"
if not os.path.exists("logs"):
    os.makedirs("logs")

with open(log_file_path, "w") as f:
    f.write("")
log_watcher = LogWatcher(log_file_path)
system = System(
    trains=args.trains,
    stations=args.stations,
    dev_mode=args.dev,
    simulate=args.simulate,
    start_port=args.port,
    log_watcher=log_watcher,
    log_file_path=log_file_path,
)

system.start()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        system.stop()
        break
    except Exception as e:
        print(f"Error: {e}")
        break
