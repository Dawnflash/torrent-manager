import xmlrpc.client
import urllib.parse
from datetime import datetime
from client import Client
from torrent import Torrent


class RTorrentClient(Client):
    def __init__(self, url, reserve_gb: int, required_labels: list[str]):
        super().__init__(reserve_gb, required_labels)
        self.proxy = xmlrpc.client.ServerProxy(url)
        self._hashes = set()  # needed for calling free_diskspace

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

        self._hashes = {torrent.infohash for torrent in torrents}
        return torrents

    def free_diskspace(self) -> int:
        """Get free disk space in bytes."""
        if len(self._hashes) == 0:
            self.list_torrents()
        if len(self._hashes) == 0:
            return int(1e18)
        for infohash in self._hashes:
            try:
                return int(self.proxy.d.free_diskspace(infohash))
            except xmlrpc.client.Fault as e:
                if e.faultCode == 1:
                    continue
                raise e
        return int(1e18)

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

    def configure(self):
        """Configure the client."""
        # pre-allocate files so that free_diskspace is more accurate
        self.proxy.system.file.allocate.set("", 1)
