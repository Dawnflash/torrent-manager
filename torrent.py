from datetime import datetime


class Torrent:
    def __init__(
        self,
        infohash: str,
        name: str,
        labels: list[str],
        started_at: datetime,
        finished_at: datetime | None,
        size: int,  # bytes
        ratio: float,
        down_rate: float,  # bps
        up_rate: float,  # bps
        state: str,
        tracker_error: str | None,
    ):
        self.infohash = infohash
        self.name = name
        self.labels = labels
        self.started_at = started_at
        self.finished_at = finished_at
        self.size = size
        self.ratio = ratio
        self.down_rate = down_rate
        self.up_rate = up_rate
        self.state = state
        self.tracker_error = tracker_error

    def __repr__(self):
        return f"Torrent(hash={self.infohash}, name={self.name}, labels={self.labels}, started_at={self.started_at}, finished_at={self.finished_at}, size={self.size}, ratio={self.ratio}, state={self.state} tracker_error={self.tracker_error}, down_rate={self.down_rate}, up_rate={self.up_rate})"
