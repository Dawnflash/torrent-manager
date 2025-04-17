import xmlrpc.client
import urllib.parse
from datetime import datetime
from client import Client
from torrent import Torrent


class RTorrentClient(Client):
    def __init__(self, url, storage_cap_gb: int, required_labels: list[str]):
        super().__init__(storage_cap_gb, required_labels)
        self.proxy = xmlrpc.client.ServerProxy(url)

    def list_torrents(self) -> list[Torrent]:
        """List torrents."""
        raw_torrents = self.proxy.d.multicall2(
            "",
            "",
            "d.hash=",
            "d.name=",
            "d.custom1=",
            "d.timestamp.started=",
            "d.timestamp.finished=",
            "d.size_bytes=",
            "d.ratio=",
            "d.message=",
        )
        torrents = [
            Torrent(
                infohash=entry[0],
                name=entry[1],
                labels=urllib.parse.unquote(entry[2]).split(",") if entry[2] else [],
                started_at=datetime.fromtimestamp(entry[3]),
                finished_at=datetime.fromtimestamp(entry[4]) if entry[4] > 0 else None,
                size=int(entry[5]),
                ratio=float(entry[6]) / 1000,
                tracker_error=entry[7] if entry[7].startswith("Tracker: ") else None,
            )
            for entry in raw_torrents
        ]

        return torrents

    def _hook_erase_event(self):
        """Add a hook that erases files when the torrent is removed."""
        self.proxy.method.set_key(
            "",
            "event.download.erased",
            "delete_erased",
            "execute=rm,-rf,--,$d.base_path=",
        )

    def _unhook_erase_event(self):
        """Remove the hook that erases files when the torrent is removed."""
        self.proxy.method.set_key("", "event.download.erased", "delete_erased")

    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""
        try:
            self._hook_erase_event()
            self.proxy.d.erase(torrent.infohash)
            self._unhook_erase_event()
            return True
        except xmlrpc.client.Fault as e:
            if e.faultCode == 1:
                return False
            raise e
