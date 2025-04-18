import xmlrpc.client
import urllib.parse
import re
from datetime import datetime
from client import Client
from torrent import Torrent


class RTorrentClient(Client):
    def __init__(self, name: str, url: str):
        super().__init__(name)
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
            "d.down.rate=",
            "d.up.rate=",
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
                down_rate=float(entry[7]) * 8,  # Bps in
                up_rate=float(entry[8]) * 8,  # Bps in
                tracker_error=(
                    re.search(r"^Tracker: \[(.*)\]$", entry[9]).group(1)
                    if entry[9].startswith("Tracker: [")
                    else None
                ),  # "Tracker: [error message]"
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
