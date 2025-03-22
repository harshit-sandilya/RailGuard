from utils import read_config
from timer import ResettableTimer
from schema import Config

config: Config = read_config()
BASE_DIR = config.data_dir
TIME_SECOND = config.time.seconds
TIMER = ResettableTimer(max_time=(24 * 60 * 60 - 1))
