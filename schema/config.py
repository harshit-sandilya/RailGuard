from pydantic import BaseModel


class Station(BaseModel):
    length: int
    width: int
    height: int


class Time(BaseModel):
    seconds: float


class Physics(BaseModel):
    friction_coefficient: float


class Train(BaseModel):
    length: int
    width: int
    height: int
    mass: int
    hp: int
    brake_force: int
    tractive_effort: int
    max_speed: int
    max_acceleration: int


class PID(BaseModel):
    kp: float
    ki: float
    kd: float


class Control(BaseModel):
    pid: PID


class Config(BaseModel):
    station: Station
    time: Time
    physics: Physics
    train: Train
    control: Control
