import sys
from datetime import datetime
from config import Config
from client import Client
from torrent import Torrent


class Tracker:
    def __init__(self, name: str):
        self.name = name
        self.config = Config.raw["trackers"][name]
        self.enabled = self.config.get("enabled", True)
        self.label = self.config["label"]
        self.requirement_sets = self.config["requirements"]
        self.storage_cap = self.config.get("storage_cap_gb", 0) * (1 << 30)
        self.unsatisfied_cap = self.config.get("unsatisfied_cap", 0)
        self.download_slots = self.config.get("download_slots", 0)

    def filter_torrents(self, client: Client, torrents: list[Torrent]) -> list[Torrent]:
        """Filter torrents from this tracker."""
        labels = client.required_labels.union([self.label])
        return [
            torrent
            for torrent in torrents
            if all(label in torrent.labels for label in labels)
        ]

    def list_torrents(self, client: Client) -> list[Torrent]:
        """List torrents from this tracker."""
        return self.filter_torrents(client, client.list_torrents())

    def evaluate_requirement(self, torrent: Torrent, name: str, value: int) -> bool:
        """Evaluate a requirement for a torrent."""
        if name == "min_seed_ratio":
            buffer = Config.raw["global"]["trackers"]["ratio_buffer"]
            return torrent.ratio >= value + buffer
        elif name == "min_seed_hours":
            age = (datetime.now() - torrent.finished_at).total_seconds() / 3600
            buffer = int(Config.raw["global"]["trackers"]["seed_buffer_hours"])
            return age >= value + buffer
        else:
            raise ValueError(f"Unknown requirement: {name}")

    def is_satisfied(self, torrent: Torrent) -> bool:
        """Check if the torrent satisfies the tracker's requirements."""
        return torrent.finished_at is not None and any(
            all(
                self.evaluate_requirement(torrent, name, value)
                for name, value in reqs.items()
            )
            for reqs in self.requirement_sets
        )

    def can_accept(self, client: Client, size: int) -> bool:
        """Check if the tracker can accept the torrent."""
        client_torrents = client.list_torrents()
        size_total = sum(torrent.size for torrent in client_torrents) + size
        if size_total > client.storage_cap:
            Config.log_message(
                f"Storage cap exceeded (client): {size_total / (1 << 30):.02f}/{client.storage_cap / (1 << 30):.02f} GiB.",
            )
            return False
        torrents = self.filter_torrents(client, client_torrents)
        if self.storage_cap > 0:
            consumed = sum(torrent.size for torrent in torrents) + size
            if consumed > self.storage_cap:
                Config.log_message(
                    f"Storage cap exceeded (tracker): {consumed / (1 << 30):.02f}/{self.storage_cap / (1 << 30):.02f} GiB.",
                )
                return False
        if self.unsatisfied_cap > 0:
            unsatisfied_torrents = [
                torrent for torrent in torrents if not self.is_satisfied(torrent)
            ]
            if len(unsatisfied_torrents) >= self.unsatisfied_cap:
                Config.log_message(
                    f"Unsatisfied cap exceeded: {unsatisfied_torrents}/{self.unsatisfied_cap}.",
                )
                return False
        if self.download_slots > 0:
            downloading = [
                torrent for torrent in torrents if torrent.finished_at is None
            ]
            if len(downloading) >= self.download_slots:
                Config.log_message(
                    f"Download slots exceeded: {len(downloading)}/{self.download_slots}.",
                )
                return False
        return True
