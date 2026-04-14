"""SQL 合併核心邏輯。"""

from __future__ import annotations

import re
from pathlib import Path

from sqlmerge_tool.models import CteDefinition, MergeSpec, OutputColumnSpec, ParsedSqlModule
from sqlmerge_tool.services.validation_service import validate_merge_spec
from sqlmerge_tool.services.validation_service import validate_sql_syntax_sqlglot, SqlValidationError
from sqlmerge_tool.services.validation_service import validate_sql_syntax_sqlglot


_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def sanitize_name(raw_name: str) -> str:
    """將檔名或 CTE 名稱轉為安全識別字。"""
    value = re.sub(r"[^A-Za-z0-9_]+", "_", raw_name.strip())
    value = value.strip("_").lower()
    if not value:
        raise ValueError("名稱不可為空白。")
    if value[0].isdigit():
        value = f"n_{value}"
    return value


def keyword_at(sql_text: str, index: int, keyword: str) -> bool:
    """判斷 index 位置是否剛好是指定關鍵字。"""
    upper_text = sql_text.upper()
    upper_keyword = keyword.upper()
    end_index = index + len(upper_keyword)
    if upper_text[index:end_index] != upper_keyword:
        return False

    before_ok = index == 0 or not (
        sql_text[index - 1].isalnum() or sql_text[index - 1] == "_"
    )
    after_ok = end_index >= len(sql_text) or not (
        sql_text[end_index].isalnum() or sql_text[end_index] == "_"
    )
    return before_ok and after_ok


def skip_space_and_comments(sql_text: str, index: int) -> int:
    """略過空白、行註解與區塊註解。"""
    length = len(sql_text)
    while index < length:
        char = sql_text[index]
        if char.isspace() or char == ";":
            index += 1
            continue
        if sql_text.startswith("--", index):
            line_break = sql_text.find("\n", index)
            if line_break == -1:
                return length
            index = line_break + 1
            continue
        if sql_text.startswith("/*", index):
            block_end = sql_text.find("*/", index + 2)
            if block_end == -1:
                raise ValueError("SQL 區塊註解未正確結束。")
            index = block_end + 2
            continue
        break
    return index


def parse_identifier(sql_text: str, index: int) -> tuple[str, int]:
    """解析未加引號的識別字。"""
    match = _IDENTIFIER_PATTERN.match(sql_text, index)
    if not match:
        raise ValueError(f"無法解析識別字，位置: {index}")
    return match.group(0), match.end()


def consume_balanced_parentheses(sql_text: str, start_index: int) -> tuple[str, int]:
    """從指定位置開始，擷取完整括號內容。"""
    if start_index >= len(sql_text) or sql_text[start_index] != "(":
        raise ValueError("consume_balanced_parentheses 必須從 '(' 開始。")

    depth = 0
    index = start_index
    length = len(sql_text)
    while index < length:
        if sql_text.startswith("--", index):
            line_break = sql_text.find("\n", index)
            if line_break == -1:
                return sql_text[start_index:length], length
            index = line_break + 1
            continue
        if sql_text.startswith("/*", index):
            block_end = sql_text.find("*/", index + 2)
            if block_end == -1:
                raise ValueError("SQL 區塊註解未正確結束。")
            index = block_end + 2
            continue

        char = sql_text[index]

        if char in ("'", '"'):
            quote = char
            index += 1
            while index < length:
                if sql_text[index] == quote:
                    if index + 1 < length and sql_text[index + 1] == quote:
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return sql_text[start_index : index + 1], index + 1
        index += 1

    raise ValueError("SQL 括號未正確配對。")


def extract_top_level_with(
    sql_text: str,
) -> tuple[list[tuple[str, str | None, str]], str, bool]:
    """抽出最外層 WITH 的 CTE 與最終 SELECT 主體。"""
    normalized_sql = sql_text.strip()
    index = skip_space_and_comments(normalized_sql, 0)
    if not keyword_at(normalized_sql, index, "WITH"):
        return [], normalized_sql.rstrip().rstrip(";"), False

    index += len("WITH")
    index = skip_space_and_comments(normalized_sql, index)
    uses_recursive = False
    if keyword_at(normalized_sql, index, "RECURSIVE"):
        uses_recursive = True
        index += len("RECURSIVE")

    ctes: list[tuple[str, str | None, str]] = []
    while True:
        index = skip_space_and_comments(normalized_sql, index)
        cte_name, index = parse_identifier(normalized_sql, index)
        index = skip_space_and_comments(normalized_sql, index)

        column_list_sql: str | None = None
        if index < len(normalized_sql) and normalized_sql[index] == "(":
            column_list_sql, index = consume_balanced_parentheses(normalized_sql, index)
            index = skip_space_and_comments(normalized_sql, index)

        if not keyword_at(normalized_sql, index, "AS"):
            raise ValueError(f"CTE {cte_name} 缺少 AS 關鍵字。")

        index += len("AS")
        index = skip_space_and_comments(normalized_sql, index)

        cte_body_with_parentheses, index = consume_balanced_parentheses(
            normalized_sql,
            index,
        )
        cte_body = cte_body_with_parentheses[1:-1].strip()
        ctes.append((cte_name, column_list_sql, cte_body))

        index = skip_space_and_comments(normalized_sql, index)
        if index < len(normalized_sql) and normalized_sql[index] == ",":
            index += 1
            continue

        final_select_sql = normalized_sql[index:].strip().rstrip(";")
        if not final_select_sql:
            raise ValueError("WITH 後面缺少最終 SELECT。")
        return ctes, final_select_sql, uses_recursive


def replace_identifiers(sql_text: str, mapping: dict[str, str]) -> str:
    """Replace identifiers outside of strings/comments using a regex-based approach.

    This implementation splits the SQL into segments (strings, line comments,
    block comments) and only runs identifier replacement on the "other" segments.
    It's significantly faster and simpler than character-by-character parsing.
    """
    if not mapping:
        return sql_text

    lower_mapping = {key.lower(): value for key, value in mapping.items()}

    # Pattern matches: single-quoted strings, double-quoted strings,
    # line comments (--...), and block comments (/* ... */).
    token_re = re.compile(r"('(?:''|[^'])*')|\"(?:\"\"|[^\"])*\"|(--[^\n]*\n?)|(/\*.*?\*/)", re.S)

    def replace_in_chunk(chunk: str) -> str:
        # replace identifiers in a chunk of SQL that's not a string/comment
        def id_replacer(m: re.Match) -> str:
            token = m.group(0)
            return lower_mapping.get(token.lower(), token)

        return _IDENTIFIER_PATTERN.sub(id_replacer, chunk)

    parts: list[str] = []
    last_end = 0
    for m in token_re.finditer(sql_text):
        # process between last_end and m.start()
        if m.start() > last_end:
            parts.append(replace_in_chunk(sql_text[last_end : m.start()]))
        # append the matched token (string/comment) unchanged
        parts.append(m.group(0))
        last_end = m.end()

    if last_end < len(sql_text):
        parts.append(replace_in_chunk(sql_text[last_end :]))

    return "".join(parts)


def parse_sql_module(sql_path: Path) -> ParsedSqlModule:
    """將一支 .sql 檔拆成 CTE 與最終 SELECT。"""
    sql_text = sql_path.read_text(encoding="utf-8")
    module_name = sanitize_name(sql_path.stem)
    ctes, final_select_sql, uses_recursive = extract_top_level_with(sql_text)

    rename_map = {
        original_name: f"{module_name}__{sanitize_name(original_name)}"
        for original_name, _column_list_sql, _body_sql in ctes
    }

    renamed_ctes = [
        CteDefinition(
            original_name=original_name,
            renamed_name=rename_map[original_name],
            column_list_sql=column_list_sql,
            body_sql=replace_identifiers(body_sql, rename_map),
        )
        for original_name, column_list_sql, body_sql in ctes
    ]

    final_select_sql = replace_identifiers(final_select_sql, rename_map)
    result_cte_name = f"{module_name}__result"

    return ParsedSqlModule(
        source_path=sql_path,
        module_name=module_name,
        ctes=renamed_ctes,
        final_select_sql=final_select_sql,
        result_cte_name=result_cte_name,
        uses_recursive_with=uses_recursive,
    )


def merge_sql_files(sql_paths: list[Path], spec: MergeSpec) -> str:
    """依規格將多支 SQL 合併成單一 SQL。"""
    validate_merge_spec(spec, sql_paths)
    parsed_modules = {
        path.name: parse_sql_module(path)
        for path in sql_paths
    }

    ordered_names = [spec.main_sql] + [join.sql_file for join in spec.joins]
    uses_recursive = any(
        parsed_modules[file_name].uses_recursive_with for file_name in ordered_names
    )

    cte_clauses: list[str] = []
    for file_name in ordered_names:
        module = parsed_modules[file_name]
        cte_clauses.extend(
            [
                (
                    f"{cte.renamed_name}{cte.column_list_sql or ''} AS (\n"
                    f"{indent_sql(cte.body_sql)}\n"
                    f")"
                )
                for cte in module.ctes
            ]
        )
        cte_clauses.append(
            (
                f"{module.result_cte_name} AS (\n"
                f"{indent_sql(module.final_select_sql)}\n"
                f")"
            )
        )

    main_module = parsed_modules[spec.main_sql]
    alias_map = {spec.main_sql: "main_src"}
    join_lines = []

    for index, join in enumerate(spec.joins, start=1):
        join_module = parsed_modules[join.sql_file]
        alias = f"join_{index}"
        alias_map[join.sql_file] = alias
        on_clause = " AND ".join(
            [
                f"main_src.{condition.main_column} = {alias}.{condition.other_column}"
                for condition in join.conditions
            ]
        )
        join_lines.append(
            f"{join.join_type} JOIN {join_module.result_cte_name} AS {alias} ON {on_clause}"
        )

    select_items = build_select_items(spec.output_columns, alias_map)

    with_keyword = "WITH RECURSIVE" if uses_recursive else "WITH"
    sql_parts = [
        with_keyword,
        ",\n".join(cte_clauses),
        "SELECT",
        "    " + ",\n    ".join(select_items),
        f"FROM {main_module.result_cte_name} AS main_src",
    ]
    sql_parts.extend(join_lines)
    merged = "\n".join(sql_parts).strip() + ";\n"
    # strict syntax check using sqlglot (optional)
    try:
        validate_sql_syntax_sqlglot(merged)
    except SqlValidationError as e:
        # Provide a short, user-friendly error while preserving original exception
        short_msg = str(e).splitlines()[0] if str(e) else "未知的語法錯誤"
        raise ValueError(f"SQL 語法檢查失敗: {short_msg}") from e
    return merged


def build_select_items(
    output_columns: list[OutputColumnSpec],
    alias_map: dict[str, str],
) -> list[str]:
    """依最終欄位規格組出 SELECT 欄位清單。"""
    if not output_columns:
        return [f"{alias}.*" for alias in alias_map.values()]

    select_items = []
    for column in output_columns:
        if not column.enabled:
            continue
        table_alias = alias_map.get(column.source_sql)
        if not table_alias:
            raise ValueError(f"找不到輸出欄位來源 SQL: {column.source_sql}")
        select_sql = f"{table_alias}.{column.column_name}"
        if column.display_name.strip():
            select_sql += f' AS {quote_identifier(column.display_name.strip())}'
        select_items.append(select_sql)

    if not select_items:
        raise ValueError("至少要保留一個最終輸出欄位。")
    return select_items


def quote_identifier(value: str) -> str:
    """對輸出欄位別名做 SQL 安全引用。"""
    return '"' + value.replace('"', '""') + '"'


def indent_sql(sql_text: str, spaces: int = 4) -> str:
    """讓輸出的 SQL 比較容易閱讀。"""
    indent = " " * spaces
    lines = [line.rstrip() for line in sql_text.strip().splitlines()]
    return "\n".join(f"{indent}{line}" if line else "" for line in lines)


def save_merged_sql(output_path: Path, sql_text: str) -> Path:
    """輸出合併結果。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql_text, encoding="utf-8")
    return output_path
