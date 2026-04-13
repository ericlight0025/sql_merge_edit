"""測試 SQL 合併輸出內容。"""

from __future__ import annotations

import unittest
from pathlib import Path

from sqlmerge_tool.models import JoinCondition, JoinSpec, MergeSpec, OutputColumnSpec
from sqlmerge_tool.services.sql_merge_service import merge_sql_files
from sqlmerge_tool.services.validation_service import load_merge_spec


class SqlMergeServiceTestCase(unittest.TestCase):
    """檢查 WITH 與 LEFT JOIN 是否有正確合併。"""

    def test_merge_sql_contains_prefixed_ctes_and_left_join(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        spec_path = project_root / "sample_data" / "merge_spec.json"
        sql_paths = sorted(sql_dir.glob("*.sql"))
        spec = load_merge_spec(spec_path)

        merged_sql = merge_sql_files(sql_paths, spec)

        self.assertIn("WITH", merged_sql)
        self.assertIn("policy_main__policy_base AS", merged_sql)
        self.assertIn("policy_main__policy_final AS", merged_sql)
        self.assertIn("policy_main__result AS", merged_sql)
        self.assertIn("LEFT JOIN customer_profile__result AS join_1", merged_sql)
        self.assertIn("LEFT JOIN risk_summary__result AS join_2", merged_sql)
        self.assertIn("main_src.customer_id = join_1.customer_id", merged_sql)
        self.assertIn("main_src.policy_id = join_4.policy_id", merged_sql)

    def test_merge_sql_supports_output_column_order_and_alias(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        sql_paths = sorted(sql_dir.glob("*.sql"))
        spec = MergeSpec(
            main_sql="policy_main.sql",
            joins=[
                load_merge_spec(project_root / "sample_data" / "merge_spec.json").joins[0],
                load_merge_spec(project_root / "sample_data" / "merge_spec.json").joins[1],
            ],
            output_columns=[
                OutputColumnSpec(
                    source_sql="customer_profile.sql",
                    column_name="customer_name",
                    enabled=True,
                    display_name="客戶名稱",
                ),
                OutputColumnSpec(
                    source_sql="policy_main.sql",
                    column_name="policy_number",
                    enabled=True,
                    display_name="保單號碼",
                ),
                OutputColumnSpec(
                    source_sql="risk_summary.sql",
                    column_name="highest_risk_level",
                    enabled=True,
                    display_name="最高風險等級",
                ),
            ],
        )

        merged_sql = merge_sql_files(sql_paths, spec)

        self.assertIn('join_1.customer_name AS "客戶名稱"', merged_sql)
        self.assertIn('main_src.policy_number AS "保單號碼"', merged_sql)
        self.assertIn('join_2.highest_risk_level AS "最高風險等級"', merged_sql)
        self.assertLess(
            merged_sql.index('join_1.customer_name AS "客戶名稱"'),
            merged_sql.index('main_src.policy_number AS "保單號碼"'),
        )

    def test_merge_sql_supports_multi_key_join(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        sql_dir = project_root / "sample_data" / "sample_sql"
        sql_paths = sorted(sql_dir.glob("*.sql"))
        spec = MergeSpec(
            main_sql="policy_main.sql",
            joins=[
                JoinSpec(
                    sql_file="claim_summary.sql",
                    join_type="LEFT",
                    conditions=[
                        JoinCondition(main_column="policy_id", other_column="policy_id"),
                        JoinCondition(main_column="customer_id", other_column="policy_id"),
                    ],
                )
            ],
        )

        merged_sql = merge_sql_files(sql_paths, spec)

        self.assertIn(
            "LEFT JOIN claim_summary__result AS join_1 ON main_src.policy_id = join_1.policy_id AND main_src.customer_id = join_1.policy_id",
            merged_sql,
        )


if __name__ == "__main__":
    unittest.main()
