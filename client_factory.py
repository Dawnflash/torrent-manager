from client import Client
from config import Config
from rtorrent import RTorrentClient
from qbittorrent import QBitTorrentClient


class ClientFactory:
    def create(self, name) -> Client:
        if name not in Config.raw["clients"]:
            raise ValueError(f"Unknown client: {name}")
        client_config = Config.raw["clients"][name]
        client_type = client_config["type"]
        if client_type == "rtorrent":
            return RTorrentClient(name, client_config["url"], client_config.get("auth"))
        elif client_type == "qbittorrent":
            return QBitTorrentClient(
                name, client_config["url"], client_config.get("auth")
            )
        else:
            raise ValueError(f"Unknown client type: {client_type}")
