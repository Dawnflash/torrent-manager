#!/usr/bin/env python3

from datetime import datetime
import yaml

from client_factory import ClientFactory
from config import Config
from tracker import Tracker
from logger import Logger


class Application:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.config = Config(config)
        self.logger = Logger(self.config.log_path)

    def check(self, client_name: str, tracker_name: str, size: int) -> tuple[bool, str]:
        """Check if a torrent can be added to the specified tracker."""
        if not client_name:
            raise ValueError("Client name is required.")
        if not tracker_name:
            raise ValueError("Tracker name is required.")
        if size <= 0:
            raise ValueError("Size must be a positive integer.")
        if client_name not in self.config.clients:
            raise ValueError(
                f"""Unknown client: {client_name}.
Available clients: {','.join(self.config.clients.keys())}"""
            )
        if tracker_name not in self.config.trackers:
            raise ValueError(
                f"""Unknown tracker: {tracker_name}.
Available trackers: {','.join(self.config.trackers.keys())}"""
            )
        tracker = Tracker(tracker_name, self.config.trackers[tracker_name])
        client = ClientFactory(self.config.clients).create(client_name)
        ok, err = tracker.can_accept(client, size)
        self.logger.log(
            f"Ingress check (client={client_name}, tracker={tracker_name}, size={size / (1 <<30 ):.02f} GiB): {err}"
        )
        return ok, err

    def manage(self, delete: bool = False):
        """List + optionally delete torrents."""
        for name in self.config.clients:
            client = ClientFactory(self.config.clients).create(name)
            client_torrents = client.filter(client.list_torrents())
            client_size_gb = sum(t.size for t in client_torrents) / (1 << 30)
            client_ratio = sum(t.uploaded for t in client_torrents) / (
                sum(t.downloaded for t in client_torrents) or 1
            )
            client_down_mbps = sum(t.down_rate for t in client_torrents) * 8 / 1e6
            client_up_mbps = sum(t.up_rate for t in client_torrents) * 8 / 1e6
            self.logger.log(
                f"Client: {name} ({len(client_torrents)} torrents, {client_size_gb:.02f} GiB, {client_ratio * 100:.0f}% ratio, ↓{client_down_mbps:.02f} Mbps, ↑{client_up_mbps:.02f} Mbps)"
            )
            for tracker_name in self.config.trackers:
                tracker = Tracker(tracker_name, self.config.trackers[tracker_name])
                if not tracker.enabled:
                    continue
                tracker_torrents = tracker.filter_torrents(client, client_torrents)
                to_delete = [
                    t
                    for t in tracker_torrents
                    if tracker.is_faulted(client, t)
                    or (tracker.is_satisfied(t) and client.is_satisfied(t))
                ]
                size_torrents_gb = sum(t.size for t in tracker_torrents) / (1 << 30)
                size_sat_gb = sum(t.size for t in to_delete) / (1 << 30)
                tracker_ratio = sum(t.uploaded for t in tracker_torrents) / (
                    sum(t.downloaded for t in tracker_torrents) or 1
                )
                tracker_down_mbps = sum(t.down_rate for t in tracker_torrents) * 8 / 1e6
                tracker_up_mbps = sum(t.up_rate for t in tracker_torrents) * 8 / 1e6
                self.logger.log(
                    f"Tracker: {tracker_name} ({len(to_delete)}/{len(tracker_torrents)} | {size_sat_gb:.02f}/{size_torrents_gb:.02f} GiB to delete, {tracker_ratio * 100:.0f}% ratio, ↓{tracker_down_mbps:.02f} Mbps, ↑{tracker_up_mbps:.02f} Mbps)"
                )
                for torrent in to_delete:
                    age_hours = (
                        (datetime.now() - torrent.finished_at).total_seconds() / 3600
                        if torrent.finished_at
                        else 0
                    )
                    is_faulted = tracker.is_faulted(client, torrent)
                    msg = "ERR" if is_faulted else "SAT"
                    msg = f"{msg}: {torrent.name}, {torrent.size / (1 << 30):.02f}GiB, {age_hours:.02f}h, {torrent.ratio() * 100:.0f}%, ↓{torrent.down_rate * 8 / 1e6:.02f} Mbps, ↑{torrent.up_rate * 8 / 1e6:.02f} Mbps"
                    if is_faulted:
                        msg += f", [{torrent.tracker_error}]"
                    self.logger.log(msg)
                    if delete:
                        client.remove_torrent(torrent)
