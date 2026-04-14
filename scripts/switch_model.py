#!/usr/bin/env python3
"""
switch_model.py

Switch opencode config between cost-first and quality-first.

Usage:
  python scripts/switch_model.py quality
  python scripts/switch_model.py cost
  python scripts/switch_model.py status

This replaces the previous shell helper and provides the same behavior on all platforms.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def usage() -> None:
    print("Usage: switch_model.py [cost|quality|status]")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        usage()
        return 2

    mode = argv[1]
    script_path = Path(__file__).resolve()
    root = script_path.parent.parent
    cost_file = root / "opencode.json"
    quality_file = root / "opencode.quality.json"
    backup = root / "opencode.cost_backup.json"

    if mode == "status":
        if not cost_file.exists():
            print(f"{cost_file} not found")
            return 1
        if not quality_file.exists():
            print(f"{quality_file} not found")
            return 1
        if md5sum(cost_file) == md5sum(quality_file):
            print("Both configs are identical.")
            return 0
        # If the active opencode.json matches the quality file we say it's active
        if md5sum(cost_file) == md5sum(quality_file):
            print("Active config matches quality-first (opencode.quality.json).")
            return 0
        print("Active config appears to be cost-first (opencode.json).")
        return 0

    if mode == "quality":
        if not quality_file.exists():
            print(f"Quality config not found: {quality_file}", file=sys.stderr)
            return 1
        # ensure backup exists
        if cost_file.exists() and not backup.exists():
            shutil.copy2(cost_file, backup)
        shutil.copy2(quality_file, cost_file)
        print("Activated quality-first (copied opencode.quality.json -> opencode.json)")
        return 0

    if mode == "cost":
        if backup.exists():
            shutil.copy2(backup, cost_file)
            print("Restored previous cost-first config (from opencode.cost_backup.json).")
            return 0
        else:
            print("No backup found; leaving opencode.json as-is.", file=sys.stderr)
            return 1

    usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
