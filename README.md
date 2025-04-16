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

Copy `config.yaml.example` to `config.yaml`, fill it in and run the script without `--check` to have it check for satisfied torrents and delete them (unless you pass `--list`). See `-h` for more details.

To get the vetting interface use the `--check` flag together with `--size`, `--tracker` and `--client`. Only 1 client is supported with `--check`.

## Supported clients

- rTorrent
- qBitTorrent (planned)

## Supported trackers

Virtually all of them, the requirements semantics are simple but flexible, allowing for both OR and AND between them (including nesting).
