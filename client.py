from abc import ABC, abstractmethod
from config import Config
from torrent import Torrent


class Client(ABC):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.config = Config.raw["clients"][name]
        self.storage_cap = self.config["storage_cap_gb"] * (1 << 30)
        self.required_labels = set(self.config["required_labels"])
        self.up_rate_cap = self.config.get("up_rate_cap_mbps", 0) * 1e6  # bps
        self.down_rate_cap = self.config.get("down_rate_cap_mbps", 0) * 1e6  # bps
        self.up_rate_threshold = (
            self.config.get("up_rate_threshold_mbps", 0) * 1e6
        )  # bps

    @abstractmethod
    def list_torrents(self) -> list[Torrent]:
        """List torrents."""

    @abstractmethod
    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""

    def configure(self):
        """Configure the client."""

    def is_satisfied(self, torrent: Torrent) -> bool:
        """Check if the torrent satisfies the client's requirements."""
        if self.up_rate_threshold > 0:
            return torrent.up_rate < self.up_rate_threshold
        return True
