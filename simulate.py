import argparse
from System import System
from LogWatcher import LogWatcher
import os

parser = argparse.ArgumentParser(
    description="Run the RailGuard simulation as a whole for a collision report"
)
parser.add_argument("--trains", type=int, help="Number of trains", required=True)
parser.add_argument("--stations", type=int, help="Number of stations", required=True)
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
    dev_mode=True,
    simulate=True,
    start_port=args.port,
    log_watcher=log_watcher,
    log_file_path=log_file_path,
)

system.start()
log_watcher.watch_blocking("== COMPLETED ==")
system.stop()
collisons = int(log_watcher.get_collisions() / 2)

print("================================================================")
print(f"Number of trains: {args.trains}")
print(f"Number of stations: {args.stations}")
print(f"Number of collisions: {collisons}")
print("================================================================")
