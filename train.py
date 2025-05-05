import ray
from ray.rllib.algorithms.ppo import PPOConfig
from rlEnv import rlEnv
from ray import tune
import os

if ray.is_initialized():
    ray.shutdown()

ray.init(local_mode=True, ignore_reinit_error=True)

if not os.path.exists("./logs"):
    os.makedirs("./logs")


tensorboard_dir = os.path.join("./logs", "tensorboard")


def env_creator():
    return rlEnv()


tune.register_env("rlEnv", env_creator)

config = (
    PPOConfig()
    .environment(rlEnv)
    .framework("torch")
    .env_runners(num_env_runners=1)
    .evaluation(evaluation_interval=None, evaluation_num_env_runners=0)
    .api_stack(
        enable_env_runner_and_connector_v2=False, enable_rl_module_and_learner=False
    )
    .training(gamma=0.9)
)

tune_config = config.to_dict()
results_path = os.path.join(os.path.dirname(__file__), "ray_results")
tune.run(
    "PPO",
    config=tune_config,
    stop={"training_iteration": 10},
    storage_path=results_path,
    checkpoint_at_end=True,
)
