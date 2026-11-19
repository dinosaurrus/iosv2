#!/usr/bin/env python3
"""Pack a SWEETXNU payload in the XNUP container used by the HakiOS loader.

The Silicium BootShim copies this container to 0xf0000000.  The UEFI
XnuLoader then selects the ``spes.payload`` entry and hands the unchanged
SWEETXNU image to the Spes loader.  Keeping the inner payload unchanged is
important: its ADT and high-memory addresses are already matched to Spes.
"""

import argparse
import struct
from pathlib import Path

MAGIC = 0x50554E58  # "XNUP"
ENTRY = struct.Struct("<16sII")


def add_entry(body: bytearray, name: str, data: bytes) -> None:
    encoded = name.encode("ascii")
    if not encoded or len(encoded) > 15:
        raise ValueError("XNUP entry names must be 1..15 ASCII bytes")
    body += ENTRY.pack(encoded, len(data), 0)
    body += data
    body += b"\0" * (-len(data) % 16)


def pack(items: list[tuple[str, Path]]) -> bytes:
    body = bytearray()
    for name, path in items:
        add_entry(body, name, path.read_bytes())
    body += b"\0" * ENTRY.size
    return struct.pack("<II", MAGIC, len(body)) + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("items", nargs="+", metavar="NAME=FILE")
    args = parser.parse_args()

    items = []
    for item in args.items:
        name, separator, filename = item.partition("=")
        if not separator or not filename:
            parser.error(f"invalid item {item!r}; expected NAME=FILE")
        items.append((name, Path(filename)))

    blob = pack(items)
    args.output.write_bytes(blob)
    print(f"{args.output}: {len(blob)} bytes")


if __name__ == "__main__":
    main()
