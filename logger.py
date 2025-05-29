import atexit
from datetime import datetime


class Logger:
    def __init__(self, log_path: str):
        self.file = open(log_path, "a", encoding="utf-8")
        atexit.register(self.file.close)

    def log(self, message: str):
        self.file.write(f"{datetime.now()}: {message}\n")
        self.file.flush()
        print(message)
