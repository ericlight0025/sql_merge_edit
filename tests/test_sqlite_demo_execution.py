"""測試 SQLite 建表、sample SQL 與合併 SQL 是否可執行。"""

from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from sqlmerge_tool.models import JoinCondition, JoinSpec, MergeSpec, OutputColumnSpec
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

    def test_all_sample_sql_files_can_run(self) -> None:
        """確保所有 sample_data/sample_sql/*.sql 都能在示範資料庫上直接執行。"""
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"

        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        for sql_path in sorted(sql_dir.glob("*.sql")):
            columns, _rows = execute_sql_file(db_path, sql_path)
            self.assertGreater(
                len(columns),
                0,
                msg=f"SQL 檔沒有輸出欄位或無法執行: {sql_path.name}",
            )

    def test_extended_merge_spec_with_recursive_and_multi_conditions_can_run(self) -> None:
        """測試更複雜的合併案例：WITH RECURSIVE + 多欄位 join 條件 + 多個 join 模組。"""
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        spec_path = project_root / "sample_data" / "merge_spec_extended_recursive.json"

        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        spec = load_merge_spec(spec_path)
        merged_sql = merge_sql_files(sorted(sql_dir.glob("*.sql")), spec)
        self.assertTrue(merged_sql.lstrip().upper().startswith("WITH RECURSIVE"))

        merged_columns, merged_rows = execute_sql(db_path, merged_sql)
        self.assertEqual(
            merged_columns,
            [
                "policy_number",
                "premium_band",
                "is_active",
                "customer_name",
                "city_group",
                "risk_count",
                "risk_bucket",
                "claim_count",
                "last_claim_date",
                "seq_no",
                "key_text",
            ],
        )
        self.assertEqual(len(merged_rows), 3)

        rows_by_policy_number = {row["policy_number"]: row for row in merged_rows}
        self.assertEqual(rows_by_policy_number["P-001"]["premium_band"], "MID")
        self.assertEqual(rows_by_policy_number["P-001"]["is_active"], 1)
        self.assertEqual(rows_by_policy_number["P-001"]["city_group"], "NORTH")
        self.assertEqual(rows_by_policy_number["P-001"]["risk_bucket"], "HIGH")
        self.assertEqual(rows_by_policy_number["P-001"]["seq_no"], 1)
        self.assertEqual(rows_by_policy_number["P-001"]["key_text"], "101-1")
        self.assertEqual(rows_by_policy_number["P-002"]["claim_count"], 2)
        self.assertEqual(rows_by_policy_number["P-002"]["last_claim_date"], "2026-03-22")
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

    def test_merge_main_without_with_and_join_with_can_execute(self) -> None:
        """主 SQL 無 WITH、join SQL 有 WITH，合併後應可執行。"""
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        with TemporaryDirectory() as temp_dir:
            temp_sql_dir = Path(temp_dir)
            main_sql_path = temp_sql_dir / "policy_plain_main.sql"
            main_sql_path.write_text(
                (
                    "SELECT\n"
                    "    p.policy_id,\n"
                    "    p.customer_id,\n"
                    "    p.policy_number\n"
                    "FROM policies AS p;\n"
                ),
                encoding="utf-8",
            )

            spec = MergeSpec(
                main_sql=main_sql_path.name,
                joins=[
                    JoinSpec(
                        sql_file="risk_summary.sql",
                        join_type="LEFT",
                        conditions=[
                            JoinCondition(
                                main_column="policy_id",
                                other_column="policy_id",
                            )
                        ],
                    )
                ],
            )
            sql_paths = [main_sql_path, sql_dir / "risk_summary.sql"]
            merged_sql = merge_sql_files(sql_paths, spec)
            merged_columns, merged_rows = execute_sql(db_path, merged_sql)

            self.assertEqual(len(merged_rows), 3)
            self.assertIn("policy_number", merged_columns)
            rows_by_policy = {row["policy_number"]: row for row in merged_rows}
            self.assertEqual(rows_by_policy["P-001"]["risk_count"], 2)
            self.assertIsNone(rows_by_policy["P-003"]["risk_count"])

    def test_merge_main_with_and_join_without_with_can_execute(self) -> None:
        """主 SQL 有 WITH、join SQL 無 WITH，合併後應可執行。"""
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        with TemporaryDirectory() as temp_dir:
            temp_sql_dir = Path(temp_dir)
            join_sql_path = temp_sql_dir / "customer_plain_join.sql"
            join_sql_path.write_text(
                (
                    "SELECT\n"
                    "    c.customer_id,\n"
                    "    c.customer_name,\n"
                    "    c.city\n"
                    "FROM customers AS c;\n"
                ),
                encoding="utf-8",
            )

            spec = MergeSpec(
                main_sql="policy_main.sql",
                joins=[
                    JoinSpec(
                        sql_file=join_sql_path.name,
                        join_type="LEFT",
                        conditions=[
                            JoinCondition(
                                main_column="customer_id",
                                other_column="customer_id",
                            )
                        ],
                    )
                ],
            )
            sql_paths = [sql_dir / "policy_main.sql", join_sql_path]
            merged_sql = merge_sql_files(sql_paths, spec)
            merged_columns, merged_rows = execute_sql(db_path, merged_sql)

            self.assertEqual(len(merged_rows), 3)
            self.assertIn("customer_name", merged_columns)
            rows_by_policy = {row["policy_number"]: row for row in merged_rows}
            self.assertEqual(rows_by_policy["P-001"]["customer_name"], "Demo Customer A")
            self.assertEqual(rows_by_policy["P-003"]["customer_name"], "Demo Customer C")

    def test_merge_both_without_with_can_execute(self) -> None:
        """主 SQL 與 join SQL 都無 WITH，合併後應可執行。"""
        project_root = Path(__file__).resolve().parents[1]
        db_path = project_root / "tests" / "_artifacts" / "demo.sqlite"
        seed_demo_database(db_path)

        with TemporaryDirectory() as temp_dir:
            temp_sql_dir = Path(temp_dir)
            main_sql_path = temp_sql_dir / "policy_plain_main.sql"
            join_sql_path = temp_sql_dir / "claim_plain_join.sql"

            main_sql_path.write_text(
                (
                    "SELECT\n"
                    "    p.policy_id,\n"
                    "    p.policy_number\n"
                    "FROM policies AS p;\n"
                ),
                encoding="utf-8",
            )
            join_sql_path.write_text(
                (
                    "SELECT\n"
                    "    c.policy_id,\n"
                    "    COUNT(*) AS claim_count\n"
                    "FROM claims AS c\n"
                    "GROUP BY c.policy_id;\n"
                ),
                encoding="utf-8",
            )

            spec = MergeSpec(
                main_sql=main_sql_path.name,
                joins=[
                    JoinSpec(
                        sql_file=join_sql_path.name,
                        join_type="LEFT",
                        conditions=[
                            JoinCondition(
                                main_column="policy_id",
                                other_column="policy_id",
                            )
                        ],
                    )
                ],
            )
            sql_paths = [main_sql_path, join_sql_path]
            merged_sql = merge_sql_files(sql_paths, spec)
            merged_columns, merged_rows = execute_sql(db_path, merged_sql)

            self.assertEqual(len(merged_rows), 3)
            self.assertIn("claim_count", merged_columns)
            rows_by_policy = {row["policy_number"]: row for row in merged_rows}
            self.assertEqual(rows_by_policy["P-002"]["claim_count"], 2)
            self.assertIsNone(rows_by_policy["P-003"]["claim_count"])


if __name__ == "__main__":
    unittest.main()
