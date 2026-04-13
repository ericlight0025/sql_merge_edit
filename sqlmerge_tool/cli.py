"""CLI 入口，便於批次驗證。"""

from __future__ import annotations

import argparse
from pathlib import Path

from sqlmerge_tool.logging_config import configure_logging
from sqlmerge_tool.services.sql_merge_service import merge_sql_files, save_merged_sql
from sqlmerge_tool.services.sqlite_demo_service import execute_sql, seed_demo_database
from sqlmerge_tool.services.validation_service import load_merge_spec


def build_argument_parser() -> argparse.ArgumentParser:
    """建立 CLI 參數。"""
    parser = argparse.ArgumentParser(description="合併多支含 WITH 的 SQL。")
    parser.add_argument(
        "--sql-dir",
        type=Path,
        default=Path("sample_data/sample_sql"),
        help="SQL 檔案所在資料夾。",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("sample_data/merge_spec.json"),
        help="合併規格 JSON 路徑。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("merged_output.sql"),
        help="合併結果輸出路徑。",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("sample_data/demo.sqlite"),
        help="SQLite 驗證資料庫路徑。",
    )
    parser.add_argument(
        "--create-demo-db",
        action="store_true",
        help="先建立示範 SQLite 資料庫。",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="建立合併 SQL 後直接對 SQLite 執行驗證。",
    )
    return parser


def main() -> None:
    """CLI 主流程。"""
    configure_logging()
    args = build_argument_parser().parse_args()
    spec = load_merge_spec(args.spec)
    sql_paths = sorted(args.sql_dir.glob("*.sql"))
    merged_sql = merge_sql_files(sql_paths, spec)
    save_merged_sql(args.output, merged_sql)
    print(f"已輸出合併 SQL: {args.output}")

    if args.create_demo_db:
        seed_demo_database(args.db)
        print(f"已建立示範 SQLite: {args.db}")

    if args.validate:
        columns, rows = execute_sql(args.db, merged_sql)
        print(f"驗證完成，欄位數: {len(columns)}，資料筆數: {len(rows)}")


if __name__ == "__main__":
    main()
