from gymnasium import Env, spaces
import numpy as np
from utils.dir_resolver import dir_resolver
from LogWatcher import LogWatcher
import os
from System import System
import time

keys = list(dir_resolver.keys())
max_index = keys.__len__() - 1


class rlEnv(Env):
    def __init__(self, config=None):
        super(rlEnv, self).__init__()
        self.objects = 4
        self.index = 0
        # self.log_file_path = f"./logs/unity_log_{self.index}.txt"
        self.port = 8080
        self.system_is_running = False
        self.collisions = 0
        self.observation = None
        self.step_count = 0

        self.observation_space = spaces.Dict(
            {
                f"train_{i}": spaces.Dict(
                    {
                        "segment": spaces.Discrete(8),
                        "next_segment": spaces.Discrete(8),
                        "speed": spaces.Box(
                            low=0.0, high=100.0, shape=(1,), dtype=np.float32
                        ),
                        "distance_remaining": spaces.Box(
                            low=0.0, high=10000.0, shape=(1,), dtype=np.float32
                        ),
                        "direction": spaces.Discrete(2),
                    }
                )
                for i in range(self.objects)
            }
        )
        self.action_space = spaces.Dict(
            {
                f"train_{i}": spaces.Dict(
                    {
                        "next_segment": spaces.Discrete(8),
                        "next_halt_time": spaces.Discrete(301),
                    }
                )
                for i in range(self.objects)
            }
        )

    def _get_initial_state(self):
        return {
            f"train_{i}": {
                "segment": np.random.randint(0, 7),
                "next_segment": np.random.randint(0, 7),
                "speed": np.array([np.random.uniform(0.0, 50.0)], dtype=np.float32),
                "distance_remaining": np.array(
                    [np.random.uniform(0.0, 500.0)], dtype=np.float32
                ),
                "direction": np.random.randint(0, 2),
            }
            for i in range(self.objects)
        }

    def reset(self, seed=None, options=None):
        print("Resetting environment...")
        super().reset(seed=seed)
        if self.system_is_running:
            self.system.stop()
            self.system_is_running = False
            del self.log_watcher
            del self.system

        self.log_file_path = (
            f"/Users/harshit/Projects/RailGuard/logs/unity_log_{self.index}.txt"
        )
        with open(self.log_file_path, "w") as f:
            f.write("")
        self.log_watcher = LogWatcher(self.log_file_path)
        self.system = System(
            trains=keys[self.index][1],
            stations=keys[self.index][0],
            dev_mode=False,
            simulate=False,
            start_port=self.port,
            log_watcher=self.log_watcher,
            log_file_path=self.log_file_path,
        )

        time.sleep(5)
        self.system.start()
        self.system_is_running = True
        self.collisions = 0
        state = self._get_initial_state()
        self.observation = state
        self.index += 1
        if self.index > max_index:
            self.index = 0
        return state, {"env_state": "reset"}

    def step(self, action):
        self.step_count += 1
        time.sleep(self.system.config.time.seconds)
        observation = self.system.global_environment.get_observation(self.objects)
        done = self.log_watcher.check_marker("== COMPLETED ==", True)
        now_collisions = self.log_watcher.get_collisions()
        is_collision = now_collisions > self.collisions
        self.collisions = now_collisions
        trucated = False
        info = {}
        reward = self.system.global_environment.process_action(
            action, is_collision, self.observation, self.step_count
        )
        self.observation = observation
        print(
            f"Step: {self.step_count}, Reward: {reward}, Done: {done} Observation: {observation}"
        )
        return observation, reward, done, trucated, info

    def close(self):
        if self.system_is_running:
            self.system.stop()
            self.system_is_running = False
        del self.log_watcher
        del self.system
        return super().close()
