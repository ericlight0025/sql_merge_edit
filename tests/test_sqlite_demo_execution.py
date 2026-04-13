"""測試 SQLite 建表、sample SQL 與合併 SQL 是否可執行。"""

from __future__ import annotations

import unittest
from pathlib import Path

from sqlmerge_tool.models import MergeSpec, OutputColumnSpec
from sqlmerge_tool.services.sql_merge_service import merge_sql_files
from sqlmerge_tool.services.sqlite_demo_service import (
    describe_sql_file_columns,
    execute_sql,
    execute_sql_file,
    seed_demo_database,
)
from sqlmerge_tool.services.validation_service import load_merge_spec


class SqliteDemoExecutionTestCase(unittest.TestCase):
    """驗證示範資料與合併結果。"""

    def test_sample_sql_and_merged_sql_can_run(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        spec_path = project_root / "sample_data" / "merge_spec.json"

        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        policy_columns, policy_rows = execute_sql_file(
            db_path,
            sql_dir / "policy_main.sql",
        )
        self.assertEqual(
            policy_columns,
            ["policy_id", "customer_id", "policy_number", "status", "premium"],
        )
        self.assertEqual(len(policy_rows), 3)

        risk_columns, risk_rows = execute_sql_file(
            db_path,
            sql_dir / "risk_summary.sql",
        )
        self.assertEqual(
            risk_columns,
            ["policy_id", "risk_count", "highest_risk_level"],
        )
        self.assertEqual(len(risk_rows), 2)

        customer_output_columns = describe_sql_file_columns(
            db_path,
            sql_dir / "customer_profile.sql",
        )
        self.assertEqual(
            customer_output_columns,
            ["customer_id", "customer_name", "city"],
        )

        spec = load_merge_spec(spec_path)
        merged_sql = merge_sql_files(sorted(sql_dir.glob("*.sql")), spec)
        merged_columns, merged_rows = execute_sql(db_path, merged_sql)

        self.assertGreater(len(merged_columns), 5)
        self.assertEqual(len(merged_rows), 3)

        rows_by_policy_number = {row["policy_number"]: row for row in merged_rows}
        self.assertEqual(rows_by_policy_number["P-001"]["customer_name"], "Demo Customer A")
        self.assertEqual(rows_by_policy_number["P-001"]["risk_count"], 2)
        self.assertEqual(rows_by_policy_number["P-001"]["highest_risk_level"], 4)
        self.assertEqual(rows_by_policy_number["P-002"]["claim_count"], 2)
        self.assertEqual(rows_by_policy_number["P-002"]["total_claim_amount"], 3000.0)
        self.assertEqual(rows_by_policy_number["P-003"]["change_count"], 1)
        self.assertIsNone(rows_by_policy_number["P-003"]["risk_count"])

    def test_custom_output_alias_columns_can_execute(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"

        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        spec = MergeSpec(
            main_sql="policy_main.sql",
            joins=[
                load_merge_spec(project_root / "sample_data" / "merge_spec.json").joins[0],
                load_merge_spec(project_root / "sample_data" / "merge_spec.json").joins[1],
            ],
            output_columns=[
                OutputColumnSpec(
                    source_sql="policy_main.sql",
                    column_name="policy_number",
                    enabled=True,
                    display_name="保單號碼",
                ),
                OutputColumnSpec(
                    source_sql="customer_profile.sql",
                    column_name="customer_name",
                    enabled=True,
                    display_name="客戶名稱",
                ),
            ],
        )

        merged_sql = merge_sql_files(sorted(sql_dir.glob("*.sql")), spec)
        merged_columns, merged_rows = execute_sql(db_path, merged_sql)

        self.assertEqual(merged_columns, ["保單號碼", "客戶名稱"])
        self.assertEqual(len(merged_rows), 3)


if __name__ == "__main__":
    unittest.main()
