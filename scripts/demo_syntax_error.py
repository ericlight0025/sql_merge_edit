#!/usr/bin/env python3
"""Demonstrate friendly SQL syntax error message produced by sqlglot validation.

This script creates a deliberately invalid SQL file and attempts to merge it.
The merge process uses sqlglot to validate syntax and will raise a concise
ValueError on failure which we print to stdout.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmerge_tool.models import MergeSpec
from sqlmerge_tool.services.sql_merge_service import merge_sql_files


def main() -> int:
    tmp_dir = Path(tempfile.mkdtemp(prefix="sqlmerge_demo_"))
    bad_sql = tmp_dir / "broken.sql"
    # deliberately invalid SQL
    bad_sql.write_text("THIS IS NOT A VALID SQL STATEMENT;", encoding="utf-8")

    spec = MergeSpec(main_sql=bad_sql.name, joins=[], output_columns=[])

    try:
        merged = merge_sql_files([bad_sql], spec)
        print("Merged SQL (unexpected):\n", merged)
        return 0
    except Exception as e:
        # Print the short, user-friendly message we expect
        print("Caught error:", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
