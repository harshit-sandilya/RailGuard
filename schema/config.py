from pydantic import BaseModel

class Entities(BaseModel):
    stations: int
    trains: int

class Station(BaseModel):
    length: int
    width: int
    height: int

class Time(BaseModel):
    multiplicator: float


class Physics(BaseModel):
    friction_coefficient: float


class Train(BaseModel):
    length: int
    width: int
    height: int
    mass: int
    hp: int
    brake_force: int
    max_speed: int
    max_acceleration: int


class PID(BaseModel):
    kp: float
    ki: float
    kd: float


class Control(BaseModel):
    pid: PID


class Server(BaseModel):
    host: str
    kafka_port: int


class Config(BaseModel):
    data_dir: str
    entities: Entities
    station: Station
    time: Time
    physics: Physics
    train: Train
    control: Control
    server: Server