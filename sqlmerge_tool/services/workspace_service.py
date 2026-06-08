"""工作區狀態的儲存與載入。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WorkspaceState:
    """GUI 完整工作區快照。

    所有路徑存為字串，tuple 存為 list，以維持 JSON 相容性。
    """
    selected_sql_paths: list[str] = field(default_factory=list)
    main_sql: str = ""
    output_path: str = ""
    db_path: str = ""
    join_field_state: dict[str, list[list[str]]] = field(default_factory=dict)
    output_column_state: dict[str, list] = field(default_factory=dict)
    output_column_order: list[str] = field(default_factory=list)


def save_workspace(path: Path, state: WorkspaceState) -> None:
    """將工作區快照寫入 JSON。"""
    payload = {
        "selected_sql_paths": state.selected_sql_paths,
        "main_sql": state.main_sql,
        "output_path": state.output_path,
        "db_path": state.db_path,
        "join_field_state": {
            k: [list(c) for c in v]
            for k, v in state.join_field_state.items()
        },
        "output_column_state": {
            k: list(v)
            for k, v in state.output_column_state.items()
        },
        "output_column_order": state.output_column_order,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_workspace(path: Path) -> WorkspaceState:
    """從 JSON 還原工作區快照。"""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return WorkspaceState(
        selected_sql_paths=payload.get("selected_sql_paths", []),
        main_sql=payload.get("main_sql", ""),
        output_path=payload.get("output_path", ""),
        db_path=payload.get("db_path", ""),
        join_field_state=payload.get("join_field_state", {}),
        output_column_state=payload.get("output_column_state", {}),
        output_column_order=payload.get("output_column_order", []),
    )
