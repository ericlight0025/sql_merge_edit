Switching opencode model configs

Overview
--------
These helpers let you switch the project's OpenCode model config between a cost-first
and quality-first configuration, and run commands temporarily under the quality config.

Files
-----
- switch_model.sh: POSIX shell helper. Usage: `scripts/switch_model.sh quality|cost|status`
- switch_model.ps1: PowerShell helper. Usage: `./scripts/switch_model.ps1 quality|cost|status`
- with_model.py: Cross-platform Python helper to run a command under the quality config and then restore the previous config.

Examples
--------
1) Activate quality config (POSIX / cross-platform Python):
   python scripts/switch_model.py quality

2) Run a command temporarily under quality config and restore (works on Windows/macOS/Linux):
   python scripts/with_model.py quality -- opencode /some/command

Notes
-----
- with_model.py creates a single backup file `opencode.cost_backup.json` the first time it runs; subsequent runs will restore from that backup.
- The scripts assume they are placed in `scripts/` at the project root (they are).
