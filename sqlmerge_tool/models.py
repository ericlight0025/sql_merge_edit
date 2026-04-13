"""資料模型定義。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class JoinCondition:
    """描述主表與其他 SQL 結果之間的欄位對應。"""

    main_column: str
    other_column: str


@dataclass(frozen=True)
class JoinSpec:
    """描述一支 SQL 要如何與主表做 JOIN。"""

    sql_file: str
    join_type: str = "LEFT"
    conditions: list[JoinCondition] = field(default_factory=list)


@dataclass(frozen=True)
class MergeSpec:
    """整體 SQL 合併規格。"""

    main_sql: str
    joins: list[JoinSpec]
    output_columns: list["OutputColumnSpec"] = field(default_factory=list)


@dataclass(frozen=True)
class OutputColumnSpec:
    """描述最終輸出的欄位、順序與顯示名稱。"""

    source_sql: str
    column_name: str
    enabled: bool = True
    display_name: str = ""


@dataclass(frozen=True)
class CteDefinition:
    """單一 CTE 的定義資訊。"""

    original_name: str
    renamed_name: str
    body_sql: str


@dataclass(frozen=True)
class ParsedSqlModule:
    """單一 .sql 檔解析後的結構。"""

    source_path: Path
    module_name: str
    ctes: list[CteDefinition]
    final_select_sql: str
    result_cte_name: str
    uses_recursive_with: bool = False
