from client import Client
from rtorrent import RTorrentClient
from qbittorrent import QBitTorrentClient


class ClientFactory:
    def __init__(self, config: dict):
        self.config = config

    def create(self, name) -> Client:
        if name not in self.config:
            raise ValueError(f"Unknown client: {name}")
        client_config = self.config[name]
        client_type = client_config["type"]
        if client_type == "rtorrent":
            return RTorrentClient(name, client_config)
        elif client_type == "qbittorrent":
            return QBitTorrentClient(name, client_config)
        else:
            raise ValueError(f"Unknown client type: {client_type}")
