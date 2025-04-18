class Config:
    @classmethod
    def __init__(cls, config: dict):
        for client in config["clients"].values():
            for k, v in config["global"]["clients"].items():
                if k not in client:
                    client[k] = v
        for tracker in config["trackers"].values():
            for k, v in config["global"]["trackers"].items():
                if k not in tracker:
                    tracker[k] = v

        cls.raw = config
