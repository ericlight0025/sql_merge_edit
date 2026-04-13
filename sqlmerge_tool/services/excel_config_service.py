"""輸出欄位設定的 Excel 匯出/匯入服務。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPE_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("", MAIN_NS)
ET.register_namespace("r", DOC_REL_NS)


@dataclass(frozen=True)
class OutputColumnExcelRow:
    """Excel 內一列輸出欄位設定。"""

    source_sql: str
    column_name: str
    enabled: bool
    display_name: str
    order: int


@dataclass(frozen=True)
class JoinConditionExcelRow:
    """Excel 內一列 join key 設定。"""

    sql_file: str
    key_order: int
    main_column: str
    other_column: str


def export_output_columns_to_excel(
    output_path: Path,
    rows: list[OutputColumnExcelRow],
) -> Path:
    """將輸出欄位設定匯出成簡單的 xlsx。"""
    header_values = ["source_sql", "column_name", "enabled", "display_name", "order"]
    body_rows = [
        [
            row.source_sql,
            row.column_name,
            "1" if row.enabled else "0",
            row.display_name,
            str(row.order),
        ]
        for row in rows
    ]
    return _export_rows_to_excel(output_path, "output_columns", header_values, body_rows)


def export_join_conditions_to_excel(
    output_path: Path,
    rows: list[JoinConditionExcelRow],
) -> Path:
    """將 join 多 key 設定匯出成簡單的 xlsx。"""
    header_values = ["sql_file", "key_order", "main_column", "other_column"]
    body_rows = [
        [
            row.sql_file,
            str(row.key_order),
            row.main_column,
            row.other_column,
        ]
        for row in rows
    ]
    return _export_rows_to_excel(output_path, "join_conditions", header_values, body_rows)


def _export_rows_to_excel(
    output_path: Path,
    sheet_name: str,
    header_values: list[str],
    body_rows: list[list[str]],
) -> Path:
    """共用 xlsx 匯出流程。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _build_content_types_xml())
        archive.writestr("_rels/.rels", _build_root_relationships_xml())
        archive.writestr("xl/workbook.xml", _build_workbook_xml(sheet_name))
        archive.writestr("xl/_rels/workbook.xml.rels", _build_workbook_relationships_xml())
        archive.writestr("xl/worksheets/sheet1.xml", _build_sheet_xml(header_values, body_rows))
    return output_path


def import_output_columns_from_excel(excel_path: Path) -> list[OutputColumnExcelRow]:
    """從 xlsx 匯入輸出欄位設定。"""
    row_dicts = _import_sheet_rows(excel_path)
    rows: list[OutputColumnExcelRow] = []
    for values in row_dicts:
        source_sql = values.get("A", "").strip()
        column_name = values.get("B", "").strip()
        enabled_raw = values.get("C", "1").strip().lower()
        display_name = values.get("D", "").strip()
        order_raw = values.get("E", "").strip()

        if not source_sql or not column_name:
            continue

        enabled = enabled_raw in {"1", "true", "yes", "y"}
        try:
            order = int(order_raw)
        except ValueError:
            order = len(rows) + 1

        rows.append(
            OutputColumnExcelRow(
                source_sql=source_sql,
                column_name=column_name,
                enabled=enabled,
                display_name=display_name,
                order=order,
            )
        )

    rows.sort(key=lambda item: item.order)
    return rows


def import_join_conditions_from_excel(excel_path: Path) -> list[JoinConditionExcelRow]:
    """從 xlsx 匯入 join 多 key 設定。"""
    row_dicts = _import_sheet_rows(excel_path)
    rows: list[JoinConditionExcelRow] = []
    for values in row_dicts:
        sql_file = values.get("A", "").strip()
        key_order_raw = values.get("B", "").strip()
        main_column = values.get("C", "").strip()
        other_column = values.get("D", "").strip()

        if not sql_file or not main_column or not other_column:
            continue

        try:
            key_order = int(key_order_raw)
        except ValueError:
            key_order = len(rows) + 1

        rows.append(
            JoinConditionExcelRow(
                sql_file=sql_file,
                key_order=key_order,
                main_column=main_column,
                other_column=other_column,
            )
        )

    rows.sort(key=lambda item: (item.sql_file.lower(), item.key_order))
    return rows


def _import_sheet_rows(excel_path: Path) -> list[dict[str, str]]:
    """讀取 sheet 內容為列字典。"""
    with ZipFile(excel_path, "r") as archive:
        sheet_xml = archive.read("xl/worksheets/sheet1.xml")
        shared_strings = (
            _load_shared_strings(archive)
            if "xl/sharedStrings.xml" in archive.namelist()
            else []
        )

    root = ET.fromstring(sheet_xml)
    sheet_data = root.find(f"{{{MAIN_NS}}}sheetData")
    if sheet_data is None:
        return []

    row_elements = sheet_data.findall(f"{{{MAIN_NS}}}row")
    if len(row_elements) <= 1:
        return []

    rows: list[dict[str, str]] = []
    for row_element in row_elements[1:]:
        values = _extract_row_values(row_element, shared_strings)
        if not values:
            continue
        rows.append(values)
    return rows


def _build_content_types_xml() -> bytes:
    root = ET.Element(
        "Types",
        xmlns=CONTENT_TYPE_NS,
    )
    ET.SubElement(
        root,
        "Default",
        Extension="rels",
        ContentType="application/vnd.openxmlformats-package.relationships+xml",
    )
    ET.SubElement(
        root,
        "Default",
        Extension="xml",
        ContentType="application/xml",
    )
    ET.SubElement(
        root,
        "Override",
        PartName="/xl/workbook.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
    )
    ET.SubElement(
        root,
        "Override",
        PartName="/xl/worksheets/sheet1.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_root_relationships_xml() -> bytes:
    root = ET.Element("Relationships", xmlns=REL_NS)
    ET.SubElement(
        root,
        "Relationship",
        Id="rId1",
        Type=f"{DOC_REL_NS}/officeDocument",
        Target="xl/workbook.xml",
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_workbook_xml(sheet_name: str) -> bytes:
    workbook = ET.Element(
        f"{{{MAIN_NS}}}workbook",
        {f"{{http://www.w3.org/2000/xmlns/}}r": DOC_REL_NS},
    )
    sheets = ET.SubElement(workbook, f"{{{MAIN_NS}}}sheets")
    ET.SubElement(
        sheets,
        f"{{{MAIN_NS}}}sheet",
        {
            f"{{{DOC_REL_NS}}}id": "rId1",
            "sheetId": "1",
            "name": sheet_name,
        },
    )
    return ET.tostring(workbook, encoding="utf-8", xml_declaration=True)


def _build_workbook_relationships_xml() -> bytes:
    root = ET.Element("Relationships", xmlns=REL_NS)
    ET.SubElement(
        root,
        "Relationship",
        Id="rId1",
        Type=f"{DOC_REL_NS}/worksheet",
        Target="worksheets/sheet1.xml",
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_sheet_xml(header_values: list[str], body_rows: list[list[str]]) -> bytes:
    worksheet = ET.Element(f"{{{MAIN_NS}}}worksheet")
    sheet_data = ET.SubElement(worksheet, f"{{{MAIN_NS}}}sheetData")

    _append_sheet_row(sheet_data, 1, header_values)

    for row_number, row_values in enumerate(body_rows, start=2):
        _append_sheet_row(sheet_data, row_number, row_values)

    return ET.tostring(worksheet, encoding="utf-8", xml_declaration=True)


def _append_sheet_row(
    sheet_data: ET.Element,
    row_number: int,
    values: list[str],
) -> None:
    row = ET.SubElement(sheet_data, f"{{{MAIN_NS}}}row", r=str(row_number))
    for column_index, value in enumerate(values, start=1):
        cell = ET.SubElement(
            row,
            f"{{{MAIN_NS}}}c",
            r=f"{_column_letter(column_index)}{row_number}",
            t="inlineStr",
        )
        inline = ET.SubElement(cell, f"{{{MAIN_NS}}}is")
        ET.SubElement(inline, f"{{{MAIN_NS}}}t").text = value


def _extract_row_values(
    row_element: ET.Element,
    shared_strings: list[str],
) -> dict[str, str]:
    values: dict[str, str] = {}
    for cell in row_element.findall(f"{{{MAIN_NS}}}c"):
        ref = cell.attrib.get("r", "")
        column = _column_part(ref)
        values[column] = _extract_cell_value(cell, shared_strings)
    return values


def _extract_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        text_node = cell.find(f"{{{MAIN_NS}}}is/{{{MAIN_NS}}}t")
        return text_node.text if text_node is not None and text_node.text is not None else ""
    if cell_type == "s":
        value_node = cell.find(f"{{{MAIN_NS}}}v")
        if value_node is None or value_node.text is None:
            return ""
        try:
            return shared_strings[int(value_node.text)]
        except (ValueError, IndexError):
            return ""
    value_node = cell.find(f"{{{MAIN_NS}}}v")
    return value_node.text if value_node is not None and value_node.text is not None else ""


def _load_shared_strings(archive: ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall(f"{{{MAIN_NS}}}si"):
        text_parts = [
            node.text or ""
            for node in item.findall(f".//{{{MAIN_NS}}}t")
        ]
        values.append("".join(text_parts))
    return values


def _column_part(cell_ref: str) -> str:
    match = re.match(r"([A-Z]+)", cell_ref)
    return match.group(1) if match else ""


def _column_letter(index: int) -> str:
    result = []
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result))
