from abc import ABC, abstractmethod
from torrent import Torrent


class Client(ABC):
    def __init__(self, name: str, config: dict):
        super().__init__()
        self.name = name
        self.config = config
        self.storage_cap = self.config["storage_cap_gb"] * (1 << 30)
        self.required_labels = set(self.config["required_labels"])
        self.up_rate_cap = self.config.get("up_rate_cap_mbps", 0) / 8 * 1e6  # Bps
        self.down_rate_cap = self.config.get("down_rate_cap_mbps", 0) / 8 * 1e6  # Bps
        self.up_rate_threshold = (
            self.config.get("up_rate_threshold_mbps", 0) / 8 * 1e6
        )  # bps

    @abstractmethod
    def list_torrents(self) -> list[Torrent]:
        """List torrents."""

    def filter(self, torrents: list[Torrent]) -> list[Torrent]:
        """Filter torrents by required labels."""
        return [
            torrent
            for torrent in torrents
            if all(label in torrent.labels for label in self.required_labels)
        ]

    @abstractmethod
    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""

    @abstractmethod
    def announce(self, torrent: Torrent):
        """Announce to the tracker."""

    def is_satisfied(self, torrent: Torrent) -> bool:
        """Check if the torrent satisfies the client's requirements."""
        if self.up_rate_threshold > 0:
            return torrent.up_rate < self.up_rate_threshold
        return True

    def is_faulted(self, torrent: Torrent) -> bool:
        """Check if the torrent is faulted. Populate tracker error if lazy-loaded."""
        return torrent.tracker_error is not None
