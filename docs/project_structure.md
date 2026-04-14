# 專案程式與文件放置位置

本檔定義目前專案的程式與 `.md` 文件位置，方便維護與歸檔。

## 1. 程式主體（Python）

- `main.py`：GUI 啟動入口
- `run_tests.py`：固定 venv 的測試執行入口（含測試報告歸檔）

## 2. 套件程式（`sqlmerge_tool/`）

- `sqlmerge_tool/__init__.py`
- `sqlmerge_tool/cli.py`
- `sqlmerge_tool/logging_config.py`
- `sqlmerge_tool/models.py`
- `sqlmerge_tool/gui/app.py`
- `sqlmerge_tool/services/excel_config_service.py`
- `sqlmerge_tool/services/sql_merge_service.py`
- `sqlmerge_tool/services/sqlite_demo_service.py`
- `sqlmerge_tool/services/validation_service.py`

## 3. 測試程式（`tests/`）

- `tests/test_excel_config_service.py`
- `tests/test_sql_merge_service.py`
- `tests/test_sqlite_demo_execution.py`

## 4. 測試輸出與歸檔

- `tests/_artifacts/`：測試過程用暫存/產物
- `tests/archive/`：測試報告歸檔資料夾（由 `run_tests.py` 產生）

## 5. 文件（`.md`）統一放在 `docs/`

- `docs/readme.md`
- `docs/plan.md`
- `docs/optimization_plan.md`
- `docs/project_structure.md`（本檔）

## 6. 其他資料

- `config/templates/`：設定範本（`join_conditions.xlsx`、`output_columns.xlsx`）
- `sample_data/`：示範資料（SQLite、sample SQL、merge spec）
- `requirements.txt`：依賴說明（目前使用內建模組）
- `backup/`：備存舊產物與清理歸檔
