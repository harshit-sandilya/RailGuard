from utils import read_config
from schema import Config

config: Config = read_config()
BASE_DIR = config.data_dir
TIME_SECOND = config.time.seconds
