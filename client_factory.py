from client import Client
from config import Config
from rtorrent import RTorrentClient


class ClientFactory:
    def create(self, name) -> Client:
        if name not in Config.raw["clients"]:
            raise ValueError(f"Unknown client: {name}")
        client_config = Config.raw["clients"][name]
        client_type = client_config["type"]
        if client_type == "rtorrent":
            return RTorrentClient(name, client_config["url"])
        else:
            raise ValueError(f"Unknown client type: {client_type}")
