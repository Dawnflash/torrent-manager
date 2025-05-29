import xmlrpc.client
import urllib.parse
import re
from datetime import datetime
from client import Client
from torrent import Torrent


class RTorrentClient(Client):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        auth = config.get("auth", None)
        url = config["url"]
        if auth:
            auth = urllib.parse.quote(f"{auth['username']}:{auth['password']}")
            url = url.replace("://", f"://{auth}@")
        self.proxy = xmlrpc.client.ServerProxy(url)

    def _get_status(self, is_open: bool, is_active: bool, msg: str) -> str:
        """Get the status of the torrent."""
        if msg.startswith("Tracker: ["):
            return "ERROR"
        if is_open and is_active:
            return "OK"
        if is_open and not is_active:
            return "PAUSED"
        return "STOPPED"

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
            "d.down.total=",
            "d.up.total=",
            "d.down.rate=",
            "d.up.rate=",
            "d.message=",
            "d.is_open=",
            "d.is_active=",
        )
        torrents = [
            Torrent(
                infohash=entry[0],
                name=entry[1],
                labels=urllib.parse.unquote(entry[2]).split(",") if entry[2] else [],
                started_at=datetime.fromtimestamp(entry[3]),
                finished_at=datetime.fromtimestamp(entry[4]) if entry[4] > 0 else None,
                size=int(entry[5]),
                downloaded=int(entry[6]),  # bytes
                uploaded=int(entry[7]),  # bytes
                down_rate=float(entry[8]) * 8,  # Bps in
                up_rate=float(entry[9]) * 8,  # Bps in
                state=self._get_status(
                    is_open=entry[11] == "1",
                    is_active=entry[12] == "1",
                    msg=entry[10],
                ),
                tracker_error=(
                    re.search(r"^Tracker: \[(.*)\]$", entry[10]).group(1)
                    if entry[10].startswith("Tracker: [")
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

    def announce(self, torrent: Torrent):
        """Announce to the tracker."""
        self.proxy.d.tracker_announce(torrent.infohash)

    def remove_torrent(self, torrent: Torrent) -> bool:
        """Remove a torrent by its infohash."""
        try:
            self.announce(torrent)  # update the tracker stats
            self._hook_erase_event()
            self.proxy.d.erase(torrent.infohash)
            self._unhook_erase_event()
            return True
        except xmlrpc.client.Fault as e:
            if e.faultCode == 1:
                return False
            raise e
