"""測試輸出欄位 Excel 匯出與匯入。"""

from __future__ import annotations

import unittest
from pathlib import Path

from sqlmerge_tool.services.excel_config_service import (
    JoinConditionExcelRow,
    OutputColumnExcelRow,
    export_join_conditions_to_excel,
    export_output_columns_to_excel,
    import_join_conditions_from_excel,
    import_output_columns_from_excel,
)


class ExcelConfigServiceTestCase(unittest.TestCase):
    """驗證 xlsx round-trip。"""

    def test_export_and_import_output_columns_excel(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        output_path = project_root / "tests" / "_artifacts" / "output_columns.xlsx"
        rows = [
            OutputColumnExcelRow(
                source_sql="policy_main.sql",
                column_name="policy_number",
                enabled=True,
                display_name="保單號碼",
                order=1,
            ),
            OutputColumnExcelRow(
                source_sql="customer_profile.sql",
                column_name="customer_name",
                enabled=False,
                display_name="客戶名稱",
                order=2,
            ),
        ]

        export_output_columns_to_excel(output_path, rows)
        loaded_rows = import_output_columns_from_excel(output_path)

        self.assertEqual(loaded_rows, rows)

    def test_export_and_import_join_conditions_excel(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        output_path = project_root / "tests" / "_artifacts" / "join_conditions.xlsx"
        rows = [
            JoinConditionExcelRow(
                sql_file="risk_summary.sql",
                key_order=1,
                main_column="policy_id",
                other_column="policy_id",
            ),
            JoinConditionExcelRow(
                sql_file="risk_summary.sql",
                key_order=2,
                main_column="customer_id",
                other_column="policy_id",
            ),
        ]

        export_join_conditions_to_excel(output_path, rows)
        loaded_rows = import_join_conditions_from_excel(output_path)

        self.assertEqual(loaded_rows, rows)


if __name__ == "__main__":
    unittest.main()
