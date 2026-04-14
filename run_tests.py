"""使用指定 venv 執行 unittest。"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
import os
from pathlib import Path


TARGET_VENV_PYTHON = Path(
    os.environ.get(
        "SQLMERGE_VENV_PYTHON",
        r"C:\DevWorkspace\googletts_package_shorts_venv\Scripts\python.exe",
    )
)


def main() -> int:
    """固定用指定 venv 跑測試，避免抓到 WindowsApps 的 python。"""
    project_root = Path(__file__).resolve().parent
    python_executable = TARGET_VENV_PYTHON if TARGET_VENV_PYTHON.exists() else Path(
        sys.executable
    )
    command = [
        str(python_executable),
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
        "-q",
    ]
    print("Running:", " ".join(command))
    result = subprocess.run(
        command,
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    output_text = (result.stdout or "") + (result.stderr or "")
    if output_text:
        print(output_text, end="" if output_text.endswith("\n") else "\n")

    archive_dir = project_root / "tests" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = archive_dir / f"test_report_{timestamp}.txt"
    latest_path = archive_dir / "latest_test_report.txt"

    report_body = "\n".join(
        [
            f"Timestamp: {datetime.now().isoformat(timespec='seconds')}",
            f"Python: {python_executable}",
            f"Command: {' '.join(command[1:])}",
            f"Return code: {result.returncode}",
            "",
            "Output:",
            output_text.rstrip(),
            "",
        ]
    )
    report_path.write_text(report_body, encoding="utf-8")
    latest_path.write_text(report_body, encoding="utf-8")
    print(f"Archived test report: {report_path}")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
