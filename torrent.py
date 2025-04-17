from datetime import datetime


class Torrent:
    def __init__(
        self,
        infohash: str,
        name: str,
        labels: list[str],
        started_at: datetime,
        finished_at: datetime | None,
        size: int,
        ratio: float,
        tracker_error: str | None,
    ):
        self.infohash = infohash
        self.name = name
        self.labels = labels
        self.started_at = started_at
        self.finished_at = finished_at
        self.size = size
        self.ratio = ratio
        self.tracker_error = tracker_error

    def __repr__(self):
        return f"Torrent(infohash={self.infohash}, name={self.name}, labels={self.labels}, started_at={self.started_at}, finished_at={self.finished_at}, size={self.size}, ratio={self.ratio} error={self.error})"
