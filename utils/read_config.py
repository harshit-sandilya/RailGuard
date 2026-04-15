import yaml

from schema import Config


def read_config() -> Config:
    with open("/Users/harshit/Projects/RailGuard/config.yaml", "r") as f:
        config = yaml.safe_load(f)
        if "friction-coefficient" in config["physics"]:
            config["physics"]["friction_coefficient"] = config["physics"].pop(
                "friction-coefficient"
            )
        if "brake-force" in config["train"]:
            config["train"]["brake_force"] = config["train"].pop("brake-force")
        if "max-acceleration" in config["train"]:
            config["train"]["max_acceleration"] = config["train"].pop(
                "max-acceleration"
            )
        if "max-speed" in config["train"]:
            config["train"]["max_speed"] = config["train"].pop("max-speed")
        if "tractive-effort" in config["train"]:
            config["train"]["tractive_effort"] = config["train"].pop("tractive-effort")
        return Config(**config)
