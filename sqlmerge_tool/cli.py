"""CLI 入口，便於批次驗證。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlmerge_tool.logging_config import configure_logging
from sqlmerge_tool.services.sql_merge_service import merge_sql_files, save_merged_sql
from sqlmerge_tool.services.sqlite_demo_service import execute_sql, seed_demo_database
from sqlmerge_tool.services.validation_service import load_merge_spec
from sqlmerge_tool.services.workspace_service import load_workspace


def build_argument_parser() -> argparse.ArgumentParser:
    """建立 CLI 參數。"""
    parser = argparse.ArgumentParser(description="合併多支含 WITH 的 SQL。")

    sql_source = parser.add_mutually_exclusive_group()
    sql_source.add_argument(
        "--sql-dir",
        type=Path,
        metavar="DIR",
        help="SQL 檔案所在資料夾（與 --sql 互斥）。",
    )
    sql_source.add_argument(
        "--sql",
        type=Path,
        action="append",
        dest="sql_files",
        metavar="FILE",
        help="指定單支 SQL 檔案，可重複使用多次（與 --sql-dir 互斥）。",
    )

    spec_source = parser.add_mutually_exclusive_group()
    spec_source.add_argument(
        "--spec",
        type=Path,
        metavar="FILE",
        help="合併規格 JSON 路徑（與 --workspace 互斥）。",
    )
    spec_source.add_argument(
        "--workspace",
        type=Path,
        metavar="FILE",
        help="從工作區快照 JSON 載入所有設定（與 --spec 互斥）。",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("merged_output.sql"),
        metavar="FILE",
        help="合併結果輸出路徑（預設: merged_output.sql）。",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("sample_data/demo.sqlite"),
        metavar="FILE",
        help="SQLite 驗證資料庫路徑（預設: sample_data/demo.sqlite）。",
    )
    parser.add_argument(
        "--create-demo-db",
        action="store_true",
        help="先建立示範 SQLite 資料庫，再執行合併。",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="建立合併 SQL 後直接對 SQLite 執行驗證。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只驗證規格與語法，不寫入輸出檔案。",
    )
    return parser


def resolve_sql_paths(args: argparse.Namespace) -> list[Path]:
    """從 --sql-dir、--sql 或 --workspace 決定要合併的 SQL 檔案清單。"""
    if args.sql_files:
        return sorted(args.sql_files)
    if args.sql_dir:
        return sorted(args.sql_dir.glob("*.sql"))
    # workspace 模式：從快照中取路徑
    if args.workspace:
        state = load_workspace(args.workspace)
        return [Path(p) for p in state.selected_sql_paths]
    # 預設：沿用舊行為，讀 sample_data/sample_sql/
    return sorted(Path("sample_data/sample_sql").glob("*.sql"))


def resolve_spec(args: argparse.Namespace) -> object:
    """從 --spec 或 --workspace 載入合併規格。"""
    if args.spec:
        return load_merge_spec(args.spec)
    if args.workspace:
        from sqlmerge_tool.services.validation_service import load_merge_spec as _load
        state = load_workspace(args.workspace)
        # workspace 不含完整 MergeSpec，需配合 --spec 或直接從 workspace 路徑旁找
        raise ValueError(
            "--workspace 模式目前需搭配 --spec 一同使用，"
            "或在工作區同目錄放置 merge_spec.json。"
        )
    return load_merge_spec(Path("sample_data/merge_spec.json"))


def main() -> None:
    """CLI 主流程。"""
    configure_logging()
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        # 建立 demo DB（可獨立執行，不依賴 spec）
        if args.create_demo_db:
            db_path = args.db
            seed_demo_database(db_path)
            print(f"已建立示範 SQLite: {db_path}")

        sql_paths = resolve_sql_paths(args)
        if not sql_paths:
            print("錯誤: 找不到任何 .sql 檔案，請確認路徑。", file=sys.stderr)
            sys.exit(1)

        spec = resolve_spec(args)
        merged_sql = merge_sql_files(sql_paths, spec)

        if args.dry_run:
            print("Dry-run 完成，規格與語法驗證通過，未寫入輸出檔案。")
        else:
            save_merged_sql(args.output, merged_sql)
            print(f"已輸出合併 SQL: {args.output}")

        if args.validate:
            columns, rows = execute_sql(args.db, merged_sql)
            print(f"SQLite 驗證完成，欄位數: {len(columns)}，資料筆數: {len(rows)}")

    except FileNotFoundError as exc:
        print(f"錯誤: 找不到檔案 — {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"錯誤: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
