class Config:
    def __init__(self, config: dict):
        for client in config["clients"].values():
            for k, v in config["global"]["clients"].items():
                if k not in client:
                    client[k] = v
        for tracker in config["trackers"].values():
            for k, v in config["global"]["trackers"].items():
                if k not in tracker:
                    tracker[k] = v

        self.clients = config["clients"]
        self.trackers = config["trackers"]
        self.log_path = config["global"]["log_path"]
        self.server = config["global"]["server"]
