from abc import ABC, abstractmethod
from torrent import Torrent


class Client(ABC):
    def __init__(self, reserve_gb: int, required_labels: set[str]):
        super().__init__()
        self.reserve_gb = reserve_gb
        self.required_labels = required_labels

    @abstractmethod
    def list_torrents(self) -> list[Torrent]:
        """List torrents."""

    @abstractmethod
    def free_diskspace(self) -> int:
        """Get free disk space in bytes."""

    @abstractmethod
    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""

    def configure(self):
        """Configure the client."""
