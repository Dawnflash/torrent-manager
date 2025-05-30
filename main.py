#!/usr/bin/env python3

import sys
import os
import argparse

from application import Application
from server import Server


def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description="Dawn's Torrent Manager")
    parser.add_argument(
        "--config",
        type=str,
        default=f"{script_dir}/config.yaml",
        help="Path to the configuration file",
    )
    subparsers = parser.add_subparsers(dest="command", description="available commands")
    check_parser = subparsers.add_parser(
        "check", help="Check if a torrent can be added"
    )
    check_parser.add_argument(
        "--client",
        type=str,
        help="Torrent client",
    )
    check_parser.add_argument("--tracker", type=str, help="Torrent tracker")
    check_parser.add_argument(
        "--size",
        type=int,
        help="Size in bytes",
    )
    manage_parser = subparsers.add_parser("manage", help="Manage torrents")
    manage_parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete satisfied torrents",
    )
    subparsers.add_parser("server", help="Run as HTTP server")

    args = parser.parse_args()

    app = Application(args.config)
    if args.command == "check":
        ok, _ = app.check(args.client, args.tracker, args.size)
        if not ok:
            sys.exit(1)
        return
    elif args.command == "manage":
        app.manage(delete=args.delete)
    elif args.command == "server":
        Server(app).run()
    else:
        print("Meow! What can I do for you?")
        parser.print_help()


if __name__ == "__main__":
    main()
