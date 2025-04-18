import atexit
from datetime import datetime


class Logger:
    @classmethod
    def __init__(cls, log_path: str):
        cls.log = open(log_path, "a", encoding="utf-8")
        atexit.register(cls.log.close)

    @classmethod
    def log_message(cls, message: str):
        cls.log.write(f"{datetime.now()}: {message}\n")
        cls.log.flush()
        print(message)
