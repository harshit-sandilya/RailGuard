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
)

tune_config = config.to_dict()
# results_path = os.path.join(os.path.dirname(__file__), "ray_results")
tune.run(
    "PPO",
    config=tune_config,
    stop={"training_iteration": 10},
    storage_path="./logs",
    checkpoint_at_end=True,
)


# algorithm = config.build_algo()

# try:
#     result = algorithm.train()
# except KeyboardInterrupt:
#     print("Training interrupted, cleaning up...")
# finally:
#     algorithm.stop()
#     ray.shutdown()
#     print("Training complete, Ray shut down.")
