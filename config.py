import atexit
from datetime import datetime


class Config:
    @classmethod
    def __init__(cls, config: dict, log: str):
        cls.raw = config
        cls.log = open(log, "a", encoding="utf-8")
        atexit.register(cls.log.close)

    @classmethod
    def log_message(cls, message: str):
        cls.log.write(f"{datetime.now()}: {message}\n")
        cls.log.flush()
        print(message)
