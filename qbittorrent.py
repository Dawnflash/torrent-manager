from datetime import datetime
import qbittorrentapi
from client import Client
from torrent import Torrent


class QBitTorrentClient(Client):
    def __init__(self, name: str, url: str, auth: dict[str, str] = None):
        super().__init__(name)
        username = None if auth is None else auth.get("username")
        password = None if auth is None else auth.get("password")
        self.client = qbittorrentapi.Client(
            host=url, username=username, password=password
        )

    def list_torrents(self) -> list[Torrent]:
        """List torrents."""
        raw = self.client.torrents_info()
        torrents = [
            Torrent(
                infohash=t.hash,
                name=t.name,
                labels=[tag.strip() for tag in t.tags.split(",")] if t.tags else [],
                started_at=datetime.fromtimestamp(t.added_on),
                finished_at=(
                    datetime.fromtimestamp(t.completion_on)
                    if t.completion_on > 0
                    else None
                ),
                size=t.size,
                downloaded=t.downloaded,
                uploaded=t.uploaded,
                down_rate=t.dlspeed,
                up_rate=t.upspeed,
                state=t.state,
                tracker_error=None,
            )
            for t in raw
        ]
        return torrents

    def announce(self, torrent: Torrent):
        """Announce to the tracker."""
        self.client.torrents_reannounce(torrent.infohash)

    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""
        self.announce(torrent)
        self.client.torrents_delete(True, torrent.infohash)
        return True

    def is_faulted(self, torrent):
        """Check if the torrent is faulted. Populate tracker error if lazy-loaded."""
        if torrent.state == "error" or torrent.tracker_error is not None:
            return True
        # Lazy load tracker error
        trackers = self.client.torrents_trackers(torrent.infohash)
        for tracker in trackers:
            # Tracker has been contacted, but it is not working (or doesn't send proper replies)
            if tracker["status"] == 4 and tracker["msg"] != "":
                torrent.tracker_error = tracker["msg"]
                return True
        return False
