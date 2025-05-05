from utils import dir_resolver, read_config
from schema import Config
from Timer import ResettableTimer
from controller import Controller, Environment
from router import Router
from dotenv import load_dotenv
import os
import subprocess
import time


class System:
    def __init__(
        self,
        trains,
        stations,
        dev_mode,
        simulate,
        start_port,
        log_watcher,
        log_file_path,
    ):
        self.trains = abs(trains)
        self.stations = stations
        self.dev_mode = dev_mode
        self.simulate = simulate
        self.start_port = start_port
        self.log_watcher = log_watcher

        config: Config = read_config()
        self.config = config
        self.global_python_timer: ResettableTimer = ResettableTimer(
            24 * 60 * 60, config.time.seconds, start_port
        )
        self.global_environment: Environment = Environment(
            start_port + 2, self.global_python_timer
        )

        load_dotenv()
        self.UNITY_PATH = os.getenv("UNITY_PATH")
        self.base_dir = dir_resolver[(stations, trains)]
        self.PROJECT_PATH = os.path.abspath(
            "/Users/harshit/Projects/RailGuard/DigitalTwin"
        )
        self.LOG_FILE = log_file_path

        self.controller = Controller(self.global_environment, trains, start_port + 1)
        self.router = Router(
            self.base_dir,
            start_port + 1,
            self.global_python_timer,
            config.train.length,
            config.station.width,
            config.time.seconds,
        )

    def start(self):
        if not self.simulate:
            self.controller.start()
        print("[unity] Launching Unity...")
        unity_args = [
            self.UNITY_PATH,
            "-projectPath",
            self.PROJECT_PATH,
            "-executeMethod",
            "CLIPlayLauncher.AutoStartPlayMode",
            "-logFile",
            self.LOG_FILE,
            "--",
            f"--startPort={self.start_port}",
            f"--trains={self.trains}",
            f"--stations={self.stations}",
        ]
        if not self.dev_mode:
            unity_args.append("-batchmode")
            unity_args.append("-nographics")
        self.proc = subprocess.Popen(unity_args)
        self.log_watcher.watch_blocking("== UNITY_PLAYMODE_START ==")
        self.log_watcher.watch_blocking("== SERVER STARTED ==")
        print("[unity] Unity is running...")
        time.sleep(5)
        self.router.start()

    def stop(self):
        if not self.simulate:
            self.controller.stop()
        self.global_python_timer.stop()
        self.global_environment.destroy()
        self.router.stop()
        print("[unity] Unity is shutting down...")
        if hasattr(self, "proc"):
            self.proc.terminate()
            self.proc.wait()
        print("[unity] Unity has been shut down.")
