#!/usr/bin/env python3
"""Generate merged SQL with per-CTE source annotations and save to files.

Creates two files in project root:
- merged_annotated.sql (from sample_data/merge_spec.json)
- merged_annotated_recursive.sql (from sample_data/merge_spec_extended_recursive.json)

This does not change library code; it uses the parser helpers to build an
annotated SQL that is easier to review.
"""
from __future__ import annotations

from pathlib import Path
import sys
from typing import List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmerge_tool.services.sql_merge_service import parse_sql_module, indent_sql
from sqlmerge_tool.services.validation_service import load_merge_spec


def build_annotated_sql(spec_path: Path) -> tuple[str, Path]:
    # spec_path is expected to be <project>/sample_data/merge_spec*.json
    project_root = spec_path.parents[1]
    sql_dir = project_root / "sample_data" / "sample_sql"
    spec = load_merge_spec(spec_path)
    sql_paths = sorted(sql_dir.glob("*.sql"))

    print(f"DEBUG: project_root={project_root}")
    print(f"DEBUG: sql_dir={sql_dir}")
    print(f"DEBUG: found sql paths: {[p.name for p in sql_paths]}")
    parsed = {}
    for p in sql_paths:
        try:
            parsed[p.name.lower()] = parse_sql_module(p)
        except Exception as exc:
            print(f"DEBUG: failed parsing {p.name}: {exc}")
    ordered_names = [spec.main_sql] + [j.sql_file for j in spec.joins]
    ordered_names = [name.lower() for name in ordered_names]

    # defend against minor naming mismatches by using lowercase keys
    uses_recursive = any(parsed[name].uses_recursive_with for name in ordered_names if name in parsed)

    parts: List[str] = []
    parts.append("WITH RECURSIVE" if uses_recursive else "WITH")

    cte_lines: List[str] = []
    for file_name in ordered_names:
        if file_name not in parsed:
            # skip missing SQL files (shouldn't happen for known sample specs)
            continue
        module = parsed[file_name]
        for cte in module.ctes:
            # cte.original_name is not directly on CteDefinition dataclass here
            # reflect from parsed module input by parsing original names from source path
            # but parse_sql_module returns CteDefinition objects with original_name attr
            orig = cte.original_name
            comment = f"-- source: {file_name}  cte: {orig}"
            clause = (
                f"{cte.renamed_name}{cte.column_list_sql or ''} AS (\n"
                f"{indent_sql(cte.body_sql)}\n"
                f")"
            )
            cte_lines.append(comment)
            cte_lines.append(clause)

        # result CTE
        comment = f"-- source: {file_name}  result"
        result_clause = (
            f"{module.result_cte_name} AS (\n{indent_sql(module.final_select_sql)}\n)"
        )
        cte_lines.append(comment)
        cte_lines.append(result_clause)

    parts.append(",\n".join(cte_lines))

    # build SELECT with joins similar to merge_sql_files but simpler: use spec ordering
    main_name = spec.main_sql.lower()
    main_module = parsed.get(main_name)
    if main_module is None:
        # fallback to first available module (shouldn't happen for correct specs)
        main_module = next(iter(parsed.values()))
        print(f"Warning: main SQL {spec.main_sql} not found; falling back to {main_module.source_path.name}")
        main_name = main_module.source_path.name.lower()
    alias_map = {main_name: "main_src"}
    join_lines: List[str] = []
    for idx, join in enumerate(spec.joins, start=1):
        alias = f"join_{idx}"
        alias_map[join.sql_file.lower()] = alias
        other_name = join.sql_file.lower()
        if other_name not in parsed:
            continue
        on_clause = " AND ".join(
            [f"main_src.{c.main_column} = {alias}.{c.other_column}" for c in join.conditions]
        )
        join_lines.append(f"{join.join_type} JOIN {parsed[other_name].result_cte_name} AS {alias} ON {on_clause}")

    select_items = [f"{alias}.*" for alias in alias_map.values()]
    parts.extend([
        "SELECT",
        "    " + ",\n    ".join(select_items),
        f"FROM {main_module.result_cte_name} AS main_src",
    ])
    parts.extend(join_lines)

    sql_text = "\n".join(parts).strip() + ";\n"
    out_name = "merged_annotated_recursive.sql" if uses_recursive else "merged_annotated.sql"
    out_path = project_root / out_name
    out_path.write_text(sql_text, encoding="utf-8")
    return sql_text, out_path


def main() -> int:
    project_root = ROOT
    spec_default = project_root / "sample_data" / "merge_spec.json"
    spec_recursive = project_root / "sample_data" / "merge_spec_extended_recursive.json"

    txt1, p1 = build_annotated_sql(spec_default)
    print(f"Wrote annotated merged SQL to: {p1}")
    txt2, p2 = build_annotated_sql(spec_recursive)
    print(f"Wrote annotated recursive merged SQL to: {p2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
