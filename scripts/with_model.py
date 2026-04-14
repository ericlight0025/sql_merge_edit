#!/usr/bin/env python3
"""
with_model.py

Usage:
  python scripts/with_model.py quality -- <command...>
  python scripts/with_model.py cost -- <command...>

This script will:
  - backup the current opencode.json to opencode.cost_backup.json (once)
  - copy the requested config (opencode.quality.json or opencode.json) into opencode.json
  - run the provided shell command
  - restore opencode.json from backup

This is intended to be used when you want to run a command under the "quality" config,
and automatically revert to the previous (cost) config afterwards.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OPENCODE = ROOT / "opencode.json"
QUALITY = ROOT / "opencode.quality.json"
BACKUP = ROOT / "opencode.cost_backup.json"


def usage_and_exit() -> None:
    print("Usage: with_model.py [quality|cost] -- <command...>")
    sys.exit(2)


def ensure_backup():
    # create a backup only if not present
    if OPENCODE.exists() and not BACKUP.exists():
        shutil.copy2(OPENCODE, BACKUP)


def activate_quality():
    if not QUALITY.exists():
        print(f"Quality config not found: {QUALITY}", file=sys.stderr)
        sys.exit(1)
    ensure_backup()
    shutil.copy2(QUALITY, OPENCODE)
    print(f"Activated quality config ({QUALITY.name} -> {OPENCODE.name})")


def restore_backup():
    if BACKUP.exists():
        shutil.copy2(BACKUP, OPENCODE)
        print(f"Restored cost config from {BACKUP.name}")
    else:
        print("No backup found; leaving opencode.json as-is", file=sys.stderr)


def run_command(cmd: list[str]) -> int:
    # Run the command in a shell for convenience, but use list to avoid shell interpolation
    print("Running:", " ".join(cmd))
    try:
        return subprocess.call(cmd)
    except Exception as e:
        print("Command failed:", e, file=sys.stderr)
        return 1


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        usage_and_exit()
    mode = argv[1]
    if argv[2] != "--":
        usage_and_exit()
    cmd = argv[3:]
    if not cmd:
        usage_and_exit()

    if mode == "quality":
        activate_quality()
        try:
            return run_command(cmd)
        finally:
            restore_backup()
    elif mode == "cost":
        # just run command under current cost config
        return run_command(cmd)
    else:
        usage_and_exit()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
