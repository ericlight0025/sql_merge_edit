#!/usr/bin/env python3
"""Generate merged SQL from sample_data and run it against demo sqlite, print columns and first rows."""
from __future__ import annotations

from pathlib import Path
import json
import sys

# Ensure project root is on sys.path so package imports work when running the script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmerge_tool.services.sqlite_demo_service import seed_demo_database, execute_sql, execute_sql_file
from sqlmerge_tool.services.sql_merge_service import merge_sql_files
from sqlmerge_tool.services.validation_service import load_merge_spec


def main() -> int:
    root = ROOT
    sql_dir = root / "sample_data" / "sample_sql"
    spec_path = root / "sample_data" / "merge_spec.json"
    db_path = root / "tests" / "_artifacts" / "demo.sqlite"

    seed_demo_database(db_path)

    spec = load_merge_spec(spec_path)
    sql_paths = sorted(sql_dir.glob("*.sql"))
    merged_sql = merge_sql_files(sql_paths, spec)

    print("-- MERGED SQL --\n")
    print(merged_sql)
    print("\n-- EXECUTE RESULT --\n")

    columns, rows = execute_sql(db_path, merged_sql)
    print("COLUMNS:", json.dumps(columns, ensure_ascii=False))

    # show first 5 rows as dicts
    out_rows = []
    for row in rows[:5]:
        out_rows.append({col: row[col] for col in columns})
    print("ROWS_PREVIEW:", json.dumps(out_rows, ensure_ascii=False))
    print(f"TOTAL_ROWS: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
