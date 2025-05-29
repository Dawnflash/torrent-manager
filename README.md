# Dawn's Torrent Manager

This is an automation script to help with [AutoBRR](https://autobrr.com/) torrent management.
It has two primary use-cases:

1. It detects when torrents are satisfied by the tracker's requirements and deletes them to free up space. This should run on a timer.
2. It serves as an external validator for AutoBRR and will only permit a torrent if its addition won't violate the tracker's or your client's terms

## Installation

```
pip3 install -r requirements.txt
```

## Usage

Copy `config.yaml.example` to `config.yaml`, fill it in and run `python3 main.py manage` to have it check for satisfied torrents. Delete them by passing `--delete`. See `-h` for more details.

To get the vetting interface use the `check` subcommand together with `--size`, `--tracker` and `--client`. Only 1 client is supported with `check`.

To get a HTTP interface use the `server` subcommand. This is useful for interacting with AutoBRR.

### Interacting with AutoBRR

First run the HTTP server like this: `python3 main.py server`. You can run this as a SystemD service:

```
[Unit]
Description=Dawn's Torrent Manager
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=1
ExecStart=/my/path/to/torrent-manager/main.py server

[Install]
WantedBy=multi-user.target
```

Start it and then point AutoBRR to it in Filter -> External: set Type to Webhook, set your endpoint, GET method, headers: `size={{ .Size }},tracker=mytracker,client=myclient` and expected code 200.

## Supported clients

- rTorrent
- qBitTorrent

## Supported trackers

Virtually all of them, the requirements semantics are simple but flexible, allowing for both OR and AND between them (including nesting).
