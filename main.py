#!/usr/bin/env python3

from datetime import datetime
import sys
import os
import argparse
import yaml

from client_factory import ClientFactory
from config import Config
from tracker import Tracker


def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description="Dawn's Torrent Manager")
    parser.add_argument(
        "--config",
        type=str,
        default=f"{script_dir}/config.yaml",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--client",
        type=str,
        help="Torrent client to use",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Only list torrents, don't remove them",
    )
    parser.add_argument(
        "--check", action="store_true", help="Check if a torrent may be added"
    )
    parser.add_argument(
        "--size",
        type=int,
        help="Size in bytes (use with --check)",
    )
    parser.add_argument(
        "--tracker", type=str, help="Tracker to check for (use with --check)"
    )
    parser.add_argument("--configure", action="store_true", help="Configure the client")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    Config(config)

    if args.check:
        if args.client is None or args.size is None or args.tracker is None:
            parser.error("--client, --size, and --tracker are required with --check")
        if args.client not in Config.raw["clients"]:
            raise ValueError(
                f"""Unknown client: {args.client}.
Available clients: {','.join(Config.raw['clients'].keys())}"""
            )
        if args.tracker not in Config.raw["trackers"]:
            raise ValueError(
                f"""Unknown tracker: {args.tracker}.
Available trackers: {','.join(Config.raw['trackers'].keys())}"""
            )
        tracker = Tracker(args.tracker)
        client = ClientFactory().create(args.client)
        if tracker.can_accept(client, args.size):
            sys.exit(0)
        else:
            sys.exit(1)

    for name in Config.raw["clients"]:
        client = ClientFactory().create(name)
        client_torrents = client.list_torrents()
        print(
            f"Client: {name} ({len(client_torrents)} torrents, {sum(t.size for t in client_torrents) / (1 << 30):.02f} GiB)"
        )
        if args.configure:
            client.configure()
        for tracker_name in Config.raw["trackers"]:
            tracker = Tracker(tracker_name)
            if not tracker.enabled:
                continue
            torrents = tracker.filter_torrents(client, client_torrents)
            to_delete = [
                t
                for t in torrents
                if tracker.is_satisfied(t) or t.tracker_error is not None
            ]
            size_torrents_gb = sum(t.size for t in torrents) / (1 << 30)
            size_sat_gb = sum(t.size for t in to_delete) / (1 << 30)
            print(
                f"Tracker: {tracker_name} ({len(to_delete)}/{len(torrents)} | {size_sat_gb:.02f}/{size_torrents_gb:.02f} GiB to delete)"
            )
            for torrent in to_delete:
                prefix = "ERR" if torrent.tracker_error is not None else "SAT"
                print(
                    f"{prefix}: {torrent.name} {(datetime.now() - torrent.finished_at).total_seconds() / 3600:.02f}h {torrent.ratio * 100:.02f}%"
                )
                if not args.list:
                    client.remove_torrent(torrent)


if __name__ == "__main__":
    main()
