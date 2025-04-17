from client import Client
from config import Config
from rtorrent import RTorrentClient


class ClientFactory:
    def create(self, name) -> Client:
        if name not in Config.raw["clients"]:
            raise ValueError(f"Unknown client: {name}")
        client_config = Config.raw["clients"][name]
        client_type = client_config["type"]
        storage_cap_gb = client_config.get("storage_cap_gb", 10)
        required_labels = set(Config.raw["global"]["clients"]["required_labels"])
        if client_type == "rtorrent":
            return RTorrentClient(
                client_config["url"],
                storage_cap_gb * (1 << 30),
                required_labels,
            )
        else:
            raise ValueError(f"Unknown client type: {client_type}")
