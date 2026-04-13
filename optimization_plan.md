# SQL Merge Tool 優化清單

## 目的

這份文件只整理後續優化方向，不直接代表現在就要實作。

原則：

1. 不破壞目前可用的 GUI / CLI 主線
2. 優先做低風險、可快速驗證、可回滾的項目
3. 先補強使用流程與驗證，再談大型重構

---

## P1：優先處理

### 1. 合併前欄位存在檢查

#### 問題

目前 join 規格與輸出欄位規格，雖然可以從 `.sql` 輸出欄位清單帶入，但在產生合併 SQL 前，仍缺少完整的 preflight 驗證。

已發生過的錯誤型態：

1. `no such column: join_3.policy_id`
2. `no such column: main_src.policy_id`

#### 建議做法

在 `產生合併 SQL` 與 `驗證合併 SQL` 前，先做欄位存在檢查：

1. 主 SQL 的 join key 是否存在於主 SQL 輸出欄位
2. 每支 join SQL 的對應 key 是否存在於該 SQL 輸出欄位
3. output columns 是否存在於對應 SQL 輸出欄位

#### 預期效益

1. 在 GUI 內就先阻擋錯誤，不用等 SQLite execute 才炸
2. 使用者能直接知道哪支 SQL、哪個欄位設定錯

---

### 2. Workspace 設定檔匯出 / 匯入

#### 問題

目前設定散落在：

1. `merge_spec.json`
2. `join_conditions.xlsx`
3. `output_columns.xlsx`

但缺少完整工作區快照。

#### 建議做法

新增一份例如 `workspace.json` 的檔案，保存：

1. 已選 SQL 清單
2. 主 SQL
3. SQLite 路徑
4. 輸出 SQL 路徑
5. Join 規格
6. 輸出欄位規格

#### 預期效益

1. 同一批 SQL 可快速恢復工作狀態
2. 不需要每次重新選檔與重設欄位

---

### 3. README 整理

#### 問題

目前 `readme.md` 仍混有早期規劃草稿與正式使用說明，閱讀成本偏高。

#### 建議做法

README 只保留：

1. 工具用途
2. GUI 啟動方式
3. CLI 使用方式
4. 可直接測試的檔案
5. 限制與已知風險

把早期提案與草稿移到獨立文件。

#### 預期效益

1. 新使用者較容易理解如何操作
2. 文件邊界更清楚

---

## P2：第二階段

### 4. GUI 狀態邏輯拆分

#### 問題

`sqlmerge_tool/gui/app.py` 目前同時負責：

1. 主題樣式
2. 畫面元件
3. join state
4. output column state
5. Excel 匯入匯出
6. merge / validate 觸發

功能再增加時，維護風險會上升。

#### 建議做法

先做低風險拆分：

1. `app.py`：只保留 GUI 與事件綁定
2. `workspace_service.py`：處理 GUI state 與 `MergeSpec` 轉換

#### 預期效益

1. 降低 GUI 類別複雜度
2. 後續比較容易補測試

---

### 5. CLI 補強

#### 問題

目前 CLI 能用，但偏向 demo 驗證用途。

#### 建議做法

補上：

1. 指定多個 `.sql` 路徑
2. 指定 workspace 設定檔
3. 驗證失敗時提供更清楚錯誤訊息

#### 預期效益

1. 更適合批次流程
2. 更容易整合到自動化

---

## P3：有需求再做

### 6. 更強的 SQL parser

#### 說明

如果未來要支援更複雜 dialect、遞迴 CTE、特殊 quoted identifier 或更複雜語法，再考慮導入正式 parser，例如 `sqlglot`。

#### 現階段判斷

這不是目前第一優先，因為現在主線痛點更偏向 GUI workflow 與驗證。

---

### 7. GUI 打包成 exe

#### 說明

等功能穩定後再做，不適合現在就投入。

#### 原因

1. 現在需求仍在變動
2. 太早打包只會增加測試與維護成本

---

## 暫不建議

### 1. 先做大型重構

目前不需要整包重寫，應維持小步快跑。

### 2. 再追加太多 GUI 花式功能

例如：

1. 拖拉排序
2. 視覺化 join graph
3. 自動中文欄名大批生成

這些都不是當前主線的 must need。

---

## 建議實作順序

1. 合併前欄位存在檢查
2. Workspace 設定檔匯出 / 匯入
3. README 整理
4. GUI 狀態邏輯拆分
5. CLI 補強

---

## 備註

若後續要開始實作，建議每次只做一項主線優化，避免一次動太多造成 GUI 行為回歸風險。
