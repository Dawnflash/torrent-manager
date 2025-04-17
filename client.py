from abc import ABC, abstractmethod
from torrent import Torrent


class Client(ABC):
    def __init__(self, storage_cap: int, required_labels: set[str]):
        super().__init__()
        self.storage_cap = storage_cap
        self.required_labels = required_labels

    @abstractmethod
    def list_torrents(self) -> list[Torrent]:
        """List torrents."""

    @abstractmethod
    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""

    def configure(self):
        """Configure the client."""
