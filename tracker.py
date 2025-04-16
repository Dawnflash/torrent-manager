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

    def list_torrents(self, client: Client):
        """List torrents from this tracker."""
        labels = client.required_labels.union([self.label])
        return [
            torrent
            for torrent in client.list_torrents()
            if all(label in torrent.labels for label in labels)
        ]

    def evaluate_requirement(self, torrent: Torrent, name: str, value: int) -> bool:
        """Evaluate a requirement for a torrent."""
        if name == "min_seed_ratio":
            return torrent.ratio >= value
        elif name == "min_seed_hours":
            age = (datetime.now() - torrent.finished_at).total_seconds() / 3600
            return age >= value
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
        free_space = client.free_diskspace()
        needed_space = size + client.reserve_gb * (1 << 30)
        if free_space < needed_space:
            print(
                f"Not enough free space. Lacking {(needed_space - free_space) / (1 << 30):.02f} GiB.",
                file=sys.stderr,
            )
            return False
        torrents = self.list_torrents(client)
        if self.storage_cap > 0:
            consumed = sum(torrent.size for torrent in torrents) + size
            if consumed > self.storage_cap:
                print(
                    f"Storage cap exceeded by {((consumed - self.storage_cap) / (1 << 30)):.02f} GiB.",
                    file=sys.stderr,
                )
                return False
        if self.unsatisfied_cap > 0:
            unsatisfied_torrents = [
                torrent for torrent in torrents if not self.is_satisfied(torrent)
            ]
            if len(unsatisfied_torrents) >= self.unsatisfied_cap:
                print(
                    f"Tracker has reached its unsatisfied cap of {self.unsatisfied_cap}.",
                    file=sys.stderr,
                )
                return False
        return True
