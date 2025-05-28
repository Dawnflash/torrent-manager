#!/usr/bin/env python3

from datetime import datetime
import sys
import os
import argparse
import yaml

from client_factory import ClientFactory
from config import Config
from tracker import Tracker
from logger import Logger


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
        "--log",
        type=str,
        default=f"{script_dir}/log.txt",
        help="Path to the log file",
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
    Logger(args.log)

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
        ok, err = tracker.can_accept(client, args.size)
        Logger.log_message(
            f"Ingress check (client={args.client}, tracker={args.tracker}, size={args.size / (1 <<30 ):.02f} GiB): {err}"
        )
        if ok:
            sys.exit(0)
        else:
            sys.exit(1)

    for name in Config.raw["clients"]:
        client = ClientFactory().create(name)
        client_torrents = client.list_torrents_filtered()
        client_size_gb = sum(t.size for t in client_torrents)
        client_ratio = sum(t.uploaded for t in client_torrents) / (
            sum(t.downloaded for t in client_torrents) or 1
        )
        Logger.log_message(
            f"Client: {name} ({len(client_torrents)} torrents, {client_size_gb:.02f} GiB, {client_ratio * 100:.02f}% avg. ratio)"
        )
        if args.configure:
            client.configure()
        for tracker_name in Config.raw["trackers"]:
            tracker = Tracker(tracker_name)
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
            Logger.log_message(
                f"Tracker: {tracker_name} ({len(to_delete)}/{len(tracker_torrents)} | {size_sat_gb:.02f}/{size_torrents_gb:.02f} GiB to delete, {tracker_ratio * 100:.02f}% avg. ratio)"
            )
            for torrent in to_delete:
                age_hours = (
                    (datetime.now() - torrent.finished_at).total_seconds() / 3600
                    if torrent.finished_at
                    else 0
                )
                is_faulted = tracker.is_faulted(client, torrent)
                msg = "ERR" if is_faulted else "SAT"
                msg = f"{msg}: {torrent.name} {torrent.size / (1 << 30):.02f}GiB {age_hours:.02f}h {torrent.ratio() * 100:.02f}%"
                if is_faulted:
                    msg += f" [{torrent.tracker_error}]"
                Logger.log_message(msg)
                if not args.list:
                    client.remove_torrent(torrent)


if __name__ == "__main__":
    main()
