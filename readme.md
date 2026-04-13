## 快速開始

### 1. 進入專案目錄

```bash
cd C:\DevWorkspace\codexcli\sqlmergeTool
```

### 2. 啟動 GUI

如果 `python` 已經指向可用的 Python 3.12：

```bash
python main.py
```

如果你的環境沒有正確設定 `python`，可直接指定完整路徑：

```bash
C:\Users\javalight\AppData\Local\Programs\Python\Python312\python.exe main.py
```

### 3. GUI 最短操作流程

1. `建立示範 SQLite`
2. `讀取 SQL 欄位`
3. 在 `工作區` 設定 `Join 規格`
4. 在 `輸出欄位` 設定最後欄位順序 / 中文 `AS`
5. `產生合併 SQL`
6. `驗證合併 SQL`

### 4. 專案目前不需要額外安裝套件

本專案目前只使用 Python 內建模組。

可參考：

- `requirements.txt`
- `sample_data/demo.sqlite`
- `merged_output.sql`
- `output_columns.xlsx`
- `join_conditions.xlsx`

### 5. 可直接測試的檔案

- Demo SQLite：`sample_data/demo.sqlite`
- Sample SQL：`sample_data/sample_sql/*.sql`
- 輸出欄位 Excel 範本：`output_columns.xlsx`
- Join 規格 Excel 範本：`join_conditions.xlsx`
- 測試產物：`tests/_artifacts/`

---

可以。
但先講白：

**如果你要可靠地把多個 `.sql` 裡面的 `WITH` 合併，最好不要只靠字串拼接。**
正確方向是：

1. 讀取每個 `.sql`
2. 找出最外層 `WITH`
3. 抽出 CTE 清單
4. 替每個 CTE 加前綴，避免撞名
5. 把原本 SQL 裡對 CTE 的引用一起改掉
6. 收集每支 SQL 的最終 `SELECT`
7. 再組成一個總 `WITH ... SELECT ...`

---

## 先講兩種做法

### 做法 A：快速版

* 用字串處理
* 適合你自己的 SQL 格式固定
* 快，但容易翻車

### 做法 B：正式版

* 用 SQL Parser
* 例如 `sqlglot`
* 比較穩，適合真的要長期用

你這題我建議直接走 **Parser 版**。

---

# 方案設計

假設你有這些檔案：

* `policy.sql`
* `risk.sql`
* `customer.sql`

每一支 SQL 可能長這樣：

```sql
WITH base_data AS (
    SELECT policy_no, cust_id
    FROM policy_main
),
final_result AS (
    SELECT *
    FROM base_data
)
SELECT *
FROM final_result
```

你希望最後變成：

```sql
WITH
policy__base_data AS (...),
policy__final_result AS (...),
risk__base_data AS (...),
risk__final_result AS (...),
customer__base_data AS (...),
customer__final_result AS (...)
SELECT ...
FROM policy__final_result p
LEFT JOIN risk__final_result r ON ...
LEFT JOIN customer__final_result c ON ...
```

---

# 完整做法

下面我直接給你一個可跑的雛形。

---

## 檔名：`merge_with_sql.py`

```python
"""
功能說明:
    讀取資料夾內多個 .sql 檔案，
    將每支 SQL 最外層 WITH 內的 CTE 抽出後重新命名，
    最後合併成單一 WITH SQL。

適用情境:
    - 多個 .sql 都有 WITH
    - 想把它們合併成一支大 SQL
    - 需要避免 CTE 名稱衝突

安裝套件:
    pip install sqlglot

注意事項:
    1. 本程式假設每支 .sql 是單一完整查詢。
    2. 本程式主要處理最外層 WITH。
    3. 若原始 SQL 有非常特殊語法，仍可能需要微調。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

import sqlglot
from sqlglot import exp


@dataclass
class SqlModule:
    """
    每個 SQL 模組的資訊。
    """
    module_name: str
    file_path: Path
    original_sql: str
    renamed_ctes: List[exp.CTE]
    final_query: exp.Expression
    final_cte_name: str


def read_sql_file(file_path: Path) -> str:
    """
    讀取 .sql 檔案內容。

    參數:
        file_path: SQL 檔案路徑

    回傳:
        SQL 純文字內容
    """
    return file_path.read_text(encoding="utf-8").strip()


def build_prefixed_name(module_name: str, original_name: str) -> str:
    """
    為 CTE 建立新的前綴名稱，避免不同 SQL 檔內的 CTE 撞名。

    例如:
        module_name = policy
        original_name = base_data
        => policy__base_data
    """
    return f"{module_name}__{original_name}"


def parse_sql(sql_text: str, dialect: str = "oracle") -> exp.Expression:
    """
    解析 SQL 字串為 sqlglot AST。

    參數:
        sql_text: SQL 文字
        dialect: SQL 方言，預設 oracle

    回傳:
        sqlglot 的 Expression 物件
    """
    return sqlglot.parse_one(sql_text, read=dialect)


def extract_top_level_with(query_expr: exp.Expression) -> Tuple[List[exp.CTE], exp.Expression]:
    """
    抽出最外層 WITH 的 CTE 清單，以及真正的主查詢主體。

    參數:
        query_expr: parse 後的 SQL AST

    回傳:
        (ctes, main_query)

    說明:
        若 SQL 沒有 WITH，則 ctes 為空陣列，main_query 為原查詢。
    """
    with_expr = query_expr.args.get("with")
    if not with_expr:
        return [], query_expr

    ctes = list(with_expr.expressions)
    main_query = query_expr.copy()
    main_query.set("with", None)
    return ctes, main_query


def rename_ctes_and_references(
    ctes: List[exp.CTE],
    main_query: exp.Expression,
    module_name: str
) -> Tuple[List[exp.CTE], exp.Expression, str]:
    """
    將同一支 SQL 中的 CTE 名稱與引用全部加上模組前綴。

    參數:
        ctes: 原本的 CTE 清單
        main_query: 原始主查詢
        module_name: 檔名對應的模組名稱

    回傳:
        renamed_ctes: 重新命名後的 CTE 清單
        renamed_main_query: 引用已同步更新的主查詢
        final_cte_name: 最後一個 CTE 的新名稱
    """
    if not ctes:
        # 若原本沒有 WITH，則把整個 main_query 包成一個最終 CTE
        fallback_name = build_prefixed_name(module_name, "final_result")
        final_cte = exp.CTE(
            this=main_query.copy(),
            alias=exp.TableAlias(this=exp.to_identifier(fallback_name))
        )
        return [final_cte], exp.select("*").from_(fallback_name), fallback_name

    # 建立舊名 -> 新名 mapping
    rename_map: Dict[str, str] = {}
    for cte in ctes:
        old_name = cte.alias_or_name
        new_name = build_prefixed_name(module_name, old_name)
        rename_map[old_name] = new_name

    # 先複製 AST，避免直接改到原物件
    renamed_ctes: List[exp.CTE] = []
    for cte in ctes:
        cte_copy = cte.copy()
        old_name = cte_copy.alias_or_name
        new_name = rename_map[old_name]

        # 修改 CTE 自己的名稱
        cte_copy.set(
            "alias",
            exp.TableAlias(this=exp.to_identifier(new_name))
        )

        # 修改 CTE 內容中對舊 CTE 名的引用
        for table in cte_copy.find_all(exp.Table):
            table_name = table.name
            if table_name in rename_map:
                table.set("this", exp.to_identifier(rename_map[table_name]))

        renamed_ctes.append(cte_copy)

    renamed_main_query = main_query.copy()

    # 修改主查詢中對舊 CTE 名的引用
    for table in renamed_main_query.find_all(exp.Table):
        table_name = table.name
        if table_name in rename_map:
            table.set("this", exp.to_identifier(rename_map[table_name]))

    # 以最後一個 CTE 視為此 SQL 的最終輸出
    last_old_name = ctes[-1].alias_or_name
    final_cte_name = rename_map[last_old_name]

    return renamed_ctes, renamed_main_query, final_cte_name


def load_sql_modules(sql_dir: Path, dialect: str = "oracle") -> List[SqlModule]:
    """
    讀取資料夾內所有 .sql，解析並建立模組資訊。

    參數:
        sql_dir: SQL 檔案資料夾
        dialect: SQL 方言

    回傳:
        SqlModule 清單
    """
    modules: List[SqlModule] = []

    for file_path in sorted(sql_dir.glob("*.sql")):
        module_name = file_path.stem.lower()
        original_sql = read_sql_file(file_path)
        parsed = parse_sql(original_sql, dialect=dialect)

        ctes, main_query = extract_top_level_with(parsed)
        renamed_ctes, renamed_main_query, final_cte_name = rename_ctes_and_references(
            ctes=ctes,
            main_query=main_query,
            module_name=module_name
        )

        modules.append(
            SqlModule(
                module_name=module_name,
                file_path=file_path,
                original_sql=original_sql,
                renamed_ctes=renamed_ctes,
                final_query=renamed_main_query,
                final_cte_name=final_cte_name
            )
        )

    return modules


def build_merged_sql(
    modules: List[SqlModule],
    main_module_name: str,
    join_specs: List[dict],
    dialect: str = "oracle"
) -> str:
    """
    依照 join 規格，將多個 SQL 模組合併成一支大 SQL。

    參數:
        modules: 已解析好的 SQL 模組
        main_module_name: 主模組名稱，例如 policy
        join_specs: join 規格清單，格式如下:
            [
                {
                    "left_module": "policy",
                    "right_module": "risk",
                    "join_type": "LEFT",
                    "on": [
                        ["policy_no", "policy_no"],
                        ["change_no", "change_no"]
                    ]
                }
            ]
        dialect: SQL 方言

    回傳:
        合併後 SQL 字串
    """
    module_map = {m.module_name: m for m in modules}

    if main_module_name not in module_map:
        raise ValueError(f"找不到主模組: {main_module_name}")

    # 收集所有 CTE
    all_ctes: List[exp.CTE] = []
    for module in modules:
        all_ctes.extend(module.renamed_ctes)

    main_module = module_map[main_module_name]

    # 建立最外層主查詢
    from_expr = exp.Table(this=exp.to_identifier(main_module.final_cte_name))
    query = exp.select("*").from_(from_expr.as_("m"))

    alias_map = {
        main_module_name: "m"
    }

    alias_counter = 1

    for spec in join_specs:
        left_module = spec["left_module"]
        right_module = spec["right_module"]
        join_type = spec.get("join_type", "LEFT").upper()
        on_pairs = spec["on"]

        if right_module not in module_map:
            raise ValueError(f"找不到右側模組: {right_module}")

        if left_module not in alias_map:
            raise ValueError(f"左側模組尚未加入主查詢: {left_module}")

        left_alias = alias_map[left_module]
        right_alias = f"t{alias_counter}"
        alias_counter += 1
        alias_map[right_module] = right_alias

        right_table = exp.Table(
            this=exp.to_identifier(module_map[right_module].final_cte_name)
        ).as_(right_alias)

        on_condition = None
        for left_col, right_col in on_pairs:
            condition = exp.column(left_col, table=left_alias).eq(
                exp.column(right_col, table=right_alias)
            )
            on_condition = condition if on_condition is None else on_condition.and_(condition)

        query = query.join(
            right_table,
            on=on_condition,
            join_type=join_type
        )

    # 把 WITH 掛回去
    merged_query = query.copy()
    merged_query.set("with", exp.With(expressions=all_ctes))

    return merged_query.sql(dialect=dialect, pretty=True)


def main() -> None:
    """
    主程式示範。

    你可以把 sql_dir 改成自己的 SQL 資料夾，
    再依照實際情況修改 join_specs。
    """
    sql_dir = Path("./sqls")
    output_file = Path("./merged_output.sql")

    modules = load_sql_modules(sql_dir=sql_dir, dialect="oracle")

    # 假設 policy.sql 為主表，其餘依序 left join
    join_specs = [
        {
            "left_module": "policy",
            "right_module": "risk",
            "join_type": "LEFT",
            "on": [
                ["policy_no", "policy_no"],
                ["change_no", "change_no"]
            ]
        },
        {
            "left_module": "policy",
            "right_module": "customer",
            "join_type": "LEFT",
            "on": [
                ["cust_id", "cust_id"]
            ]
        }
    ]

    merged_sql = build_merged_sql(
        modules=modules,
        main_module_name="policy",
        join_specs=join_specs,
        dialect="oracle"
    )

    output_file.write_text(merged_sql, encoding="utf-8")
    print(f"合併完成，輸出檔案: {output_file}")


if __name__ == "__main__":
    main()
```

---

# 目錄結構範例

```text
project/
├─ merge_with_sql.py
└─ sqls/
   ├─ policy.sql
   ├─ risk.sql
   └─ customer.sql
```

---

# 範例 SQL

## 檔名：`sqls/policy.sql`

```sql
WITH policy_base AS (
    SELECT
        policy_no,
        change_no,
        cust_id
    FROM policy_main
),
policy_final AS (
    SELECT
        policy_no,
        change_no,
        cust_id
    FROM policy_base
)
SELECT *
FROM policy_final
```

---

## 檔名：`sqls/risk.sql`

```sql
WITH risk_base AS (
    SELECT
        policy_no,
        change_no,
        risk_level
    FROM risk_table
),
risk_final AS (
    SELECT
        policy_no,
        change_no,
        risk_level
    FROM risk_base
)
SELECT *
FROM risk_final
```

---

## 檔名：`sqls/customer.sql`

```sql
WITH customer_base AS (
    SELECT
        cust_id,
        cust_name
    FROM customer_table
),
customer_final AS (
    SELECT
        cust_id,
        cust_name
    FROM customer_base
)
SELECT *
FROM customer_final
```

---

# 執行方式

```bash
pip install sqlglot
python merge_with_sql.py
```

---

# 這支程式做了什麼

它會把原本各自的 CTE 名稱改成像這樣：

* `policy__policy_base`
* `policy__policy_final`
* `risk__risk_base`
* `risk__risk_final`
* `customer__customer_base`
* `customer__customer_final`

最後輸出成一支總 SQL。

---

# 你要注意的現實問題

這題最麻煩的不是讀 `.sql`，而是下面這三件事：

## 1. 哪一個是每支 SQL 的最終輸出

我上面先假設：

* **最後一個 CTE** 就是最終輸出

如果你的 SQL 是：

```sql
WITH a AS (...),
b AS (...)
SELECT *
FROM a
```

那就不一定是最後一個 CTE。
這時候要改成：

* 解析主查詢 `FROM` 的來源
* 找出真正被 select 的那個 CTE

這可以再強化。

---

## 2. 有些 SQL 沒有 WITH

我上面已經幫你補了 fallback：

* 若沒有 WITH
* 就把整支查詢包成 `${module_name}__final_result`

所以不會直接炸。

---

## 3. CTE 內部如果有更深層、更複雜的 table alias / 子查詢

這支程式先處理主要情境：

* `FROM cte_name`
* `JOIN cte_name`

一般夠用。
但如果你 SQL 很妖，例如：

* recursive CTE
* vendor-specific hint
* 特殊函式
* 層層 nested query

還是要逐步測。

---

# 如果你不要 parser，硬字串行不行？

可以，但我不推薦。
因為你遲早會踩這些雷：

* `WITH` 出現在註解
* `WITH` 出現在字串
* 括號層級抓錯
* 多個 CTE 用逗號分隔，分一半炸掉
* alias 沒同步改

這種很像拿美工刀拆炸彈。

---

# 我建議你的實戰版本

你現在最適合的是做成這種：

1. `sqls/` 放原始 SQL
2. `mapping.json` 設定：

   * 主 SQL
   * join 順序
   * join key
3. Python 程式自動輸出 `merged_output.sql`

這樣你之後就能重複跑。

---

# 一句話結論

Python 要讀 `.sql` 再把多支含 `WITH` 的 SQL 合併，**正確做法是先 parse SQL，抽出 CTE，重新命名後再統一組成一個最外層 WITH**。
不要直接用字串硬拼，不然很快就會把自己拼進急診室。

如果你要，我下一則可以直接補你第二版：

**`mapping.json` 驅動版**
也就是：

* 自動掃描 `sqls/`
* 由 JSON 指定主表、join key、join type
* 直接產出合併 SQL

這版會更接近你真的能拿去用的工具。
