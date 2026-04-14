"""規格讀寫與驗證。"""

from __future__ import annotations

import json
from pathlib import Path

from sqlmerge_tool.models import JoinCondition, JoinSpec, MergeSpec, OutputColumnSpec

try:
    import sqlglot
    from sqlglot.errors import ParseError
except Exception:  # pragma: no cover - optional dependency
    sqlglot = None
    ParseError = Exception


class SqlValidationError(Exception):
    """Raised when SQL syntax validation fails (sqlglot).

    This allows callers to present a short, user-friendly message while
    preserving the underlying exception for debugging.
    """
    pass


def load_merge_spec(spec_path: Path) -> MergeSpec:
    """從 JSON 載入合併規格。"""
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    joins = [
        JoinSpec(
            sql_file=item["sql_file"],
            join_type=item.get("join_type", "LEFT").upper(),
            conditions=[
                JoinCondition(
                    main_column=condition["main_column"],
                    other_column=condition["other_column"],
                )
                for condition in item.get("conditions", [])
            ],
        )
        for item in payload.get("joins", [])
    ]
    output_columns = [
        OutputColumnSpec(
            source_sql=item["source_sql"],
            column_name=item["column_name"],
            enabled=item.get("enabled", True),
            display_name=item.get("display_name", ""),
        )
        for item in payload.get("output_columns", [])
    ]
    return MergeSpec(
        main_sql=payload["main_sql"],
        joins=joins,
        output_columns=output_columns,
    )


def save_merge_spec(spec_path: Path, spec: MergeSpec) -> None:
    """將合併規格輸出成 JSON。"""
    payload = {
        "main_sql": spec.main_sql,
        "joins": [
            {
                "sql_file": join.sql_file,
                "join_type": join.join_type,
                "conditions": [
                    {
                        "main_column": condition.main_column,
                        "other_column": condition.other_column,
                    }
                    for condition in join.conditions
                ],
            }
            for join in spec.joins
        ],
        "output_columns": [
            {
                "source_sql": column.source_sql,
                "column_name": column.column_name,
                "enabled": column.enabled,
                "display_name": column.display_name,
            }
            for column in spec.output_columns
        ],
    }
    spec_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def validate_merge_spec(spec: MergeSpec, sql_paths: list[Path]) -> None:
    """檢查規格與選取的 SQL 檔案是否一致。"""
    if not sql_paths:
        raise ValueError("至少要選取一個 .sql 檔案。")

    file_names = {path.name for path in sql_paths}

    if spec.main_sql not in file_names:
        raise ValueError(f"主 SQL 不在已選檔案內: {spec.main_sql}")

    seen_files: set[str] = set()
    for join in spec.joins:
        if join.sql_file == spec.main_sql:
            raise ValueError("主 SQL 不能同時出現在 joins 內。")
        if join.sql_file not in file_names:
            raise ValueError(f"Join SQL 不在已選檔案內: {join.sql_file}")
        if join.sql_file in seen_files:
            raise ValueError(f"Join SQL 重複設定: {join.sql_file}")
        seen_files.add(join.sql_file)

        if join.join_type.upper() != "LEFT":
            raise ValueError("目前 MVP 只支援 LEFT JOIN。")
        if not join.conditions:
            raise ValueError(f"{join.sql_file} 至少要設定一組 join 條件。")

        for condition in join.conditions:
            if not condition.main_column.strip() or not condition.other_column.strip():
                raise ValueError(f"{join.sql_file} 的 join 欄位不可為空白。")

    if spec.output_columns:
        if not any(column.enabled for column in spec.output_columns):
            raise ValueError("至少要勾選一個最終輸出欄位。")

    for column in spec.output_columns:
        if column.source_sql not in file_names:
            raise ValueError(f"輸出欄位來源 SQL 不在已選檔案內: {column.source_sql}")
        if not column.column_name.strip():
            raise ValueError("輸出欄位名稱不可為空白。")


def validate_sql_syntax_sqlglot(sql_text: str) -> None:
    """Use sqlglot to validate merged SQL syntax for SQLite dialect.

    Raises a ValueError with the parse error message when parsing fails.
    If sqlglot is not installed, this is a no-op.
    """
    if sqlglot is None:
        # Optional dependency not installed; skip strict validation.
        return
    try:
        # parse_one can raise ParseError on invalid syntax
        sqlglot.parse_one(sql_text, read="sqlite")
    except ParseError as e:
        # Raise a specific exception so callers can display a concise message
        raise SqlValidationError(str(e)) from e
