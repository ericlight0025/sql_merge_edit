# SQL Merge 全情境測試計畫（plan.md）

## 1. 目標

- 建立一份可重複執行的測試矩陣，涵蓋 SQL 合併工具核心情境與邊界情境。
- 所有情境都必須轉成自動化測試，且在指定環境下一次跑完全部通過。
- 測試優先順序：先保產線穩定（P0），再補邊界與防呆（P1/P2）。

## 2. 測試執行標準

- 固定執行環境：`C:\DevWorkspace\googletts_package_shorts_venv\Scripts\python.exe`
- 測試命令：
  - `C:\DevWorkspace\googletts_package_shorts_venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -q`
- 通過標準：
  - 無任何 failed / error
  - `return code = 0`
  - 覆蓋清單中每個情境皆有對應測試案例

## 3. 情境矩陣（全部要有測試）

### P0：核心可執行情境（必須先全過）

- [x] `S001` 單支 sample SQL 可直接執行（逐檔驗證）
- [x] `S002` 基本合併（main + 多個 join）可執行且資料列數正確
- [x] `S003` 主 SQL 有 `WITH`、join SQL 有 `WITH`
- [x] `S004` 主 SQL 無 `WITH`、join SQL 有 `WITH`
- [x] `S005` 主 SQL 有 `WITH`、join SQL 無 `WITH`
- [x] `S006` 主 SQL 無 `WITH`、join SQL 無 `WITH`
- [x] `S007` `WITH RECURSIVE` 參與合併後可執行
- [x] `S008` 多欄位 join 條件（AND）可執行
- [x] `S009` `LEFT JOIN` 空值情境（右表缺資料）結果正確
- [x] `S010` 指定輸出欄位、順序、別名（含中文）結果正確
- [x] `S011` CTE 欄位清單語法 `cte(col1, col2)` 合併後可執行
- [x] `S012` CTE 命名衝突時自動前綴後仍可執行

### P1：規格驗證與錯誤防呆（避免壞設定進產線）

- [ ] `S101` `main_sql` 不在檔案清單內應拋錯
- [ ] `S102` join SQL 重複設定應拋錯
- [ ] `S103` join SQL 設為 main SQL 應拋錯
- [ ] `S104` join type 非 `LEFT` 應拋錯
- [ ] `S105` join conditions 為空應拋錯
- [ ] `S106` join key 欄位空白應拋錯
- [ ] `S107` output columns 全部 disabled 應拋錯
- [ ] `S108` output column `source_sql` 不存在應拋錯
- [ ] `S109` output column 名稱空白應拋錯
- [ ] `S110` 無任何 SQL 檔案輸入應拋錯

### P2：SQL 內容邊界情境（避免 parser/replace 誤傷）

- [ ] `S201` 註解中含 CTE 名稱不應被誤替換
- [ ] `S202` 字串常值中含 CTE 名稱不應被誤替換
- [ ] `S203` 區塊註解未關閉應拋錯
- [ ] `S204` 括號不平衡應拋錯
- [ ] `S205` CTE 缺少 `AS` 應拋錯
- [ ] `S206` SQL 含分號/空白/註解前後綴時仍可正確解析
- [ ] `S207` 輸出欄位重名情境（未 alias）可執行且可觀察
- [ ] `S208` 檔名含特殊字元，`sanitize_name` 後仍可執行

### P3：周邊功能情境（配置匯入匯出）

- [x] `S301` 輸出欄位 Excel 匯出再匯入 round-trip
- [x] `S302` join 條件 Excel 匯出再匯入 round-trip
- [ ] `S303` Excel 欄位缺漏/型別錯誤時應有明確錯誤訊息

## 4. 執行順序（MVP 優先）

1. 先鎖定 P0：確保所有可執行核心情境穩定，避免影響主線。
2. 再補 P1：把壞設定擋在進合併流程之前。
3. 最後補 P2/P3：降低長期維護風險與回歸成本。

## 5. 驗收條件（Definition of Done）

- `plan.md` 列出的情境都有對應測試函式。
- 在指定 venv 跑完整測試，結果全綠。
- 新增情境後，舊情境不得退化（回歸測試全通過）。
