#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmerge_tool.services.validation_service import load_merge_spec
from sqlmerge_tool.services.sql_merge_service import merge_sql_files
from sqlmerge_tool.services.sqlite_demo_service import seed_demo_database, execute_sql


def main() -> int:
    sql_dir = ROOT / 'sample_data' / 'sample_sql'
    spec_path = ROOT / 'sample_data' / 'merge_spec_extended_recursive.json'
    db_path = ROOT / 'tests' / '_artifacts' / 'demo_recursive.sqlite'

    seed_demo_database(db_path)
    spec = load_merge_spec(spec_path)
    merged_sql = merge_sql_files(sorted(sql_dir.glob('*.sql')), spec)

    print('--- MERGED SQL (recursive) ---')
    print(merged_sql)
    print('\n--- EXECUTE RESULT ---')
    cols, rows = execute_sql(db_path, merged_sql)
    print('COLUMNS:', cols)
    print('ROWS:', len(rows))
    for r in rows:
        print(dict(r))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
