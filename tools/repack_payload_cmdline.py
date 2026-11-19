#!/usr/bin/env python3
"""Copy a SWEETXNU payload while replacing its bounded boot command line."""

import argparse
from pathlib import Path

CMDLINE_OFFSET = 0x48
CMDLINE_LENGTH = 608


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("cmdline")
    args = parser.parse_args()

    blob = bytearray(args.source.read_bytes())
    encoded = args.cmdline.encode("ascii")
    if len(encoded) >= CMDLINE_LENGTH:
        parser.error("cmdline must fit in the SWEETXNU 608-byte field")
    blob[CMDLINE_OFFSET:CMDLINE_OFFSET + CMDLINE_LENGTH] = b"\0" * CMDLINE_LENGTH
    blob[CMDLINE_OFFSET:CMDLINE_OFFSET + len(encoded)] = encoded
    args.output.write_bytes(blob)
    print(f"{args.output}: {len(blob)} bytes")


if __name__ == "__main__":
    main()
