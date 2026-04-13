"""Tkinter GUI。"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sqlmerge_tool.logging_config import configure_logging
from sqlmerge_tool.models import JoinCondition, JoinSpec, MergeSpec, OutputColumnSpec
from sqlmerge_tool.services.excel_config_service import (
    JoinConditionExcelRow,
    OutputColumnExcelRow,
    export_join_conditions_to_excel,
    export_output_columns_to_excel,
    import_join_conditions_from_excel,
    import_output_columns_from_excel,
)
from sqlmerge_tool.services.sql_merge_service import merge_sql_files, save_merged_sql
from sqlmerge_tool.services.sqlite_demo_service import (
    describe_sql_file_columns,
    execute_sql,
    seed_demo_database,
)
from sqlmerge_tool.services.validation_service import load_merge_spec, save_merge_spec


class SqlMergeApp:
    """GUI 主視窗。"""

    BG = "#0b1220"
    SURFACE = "#131c2f"
    SURFACE_ALT = "#1a2640"
    PANEL = "#101827"
    BORDER = "#26344f"
    TEXT = "#e7edf7"
    MUTED = "#8ea0bf"
    ACCENT = "#50e3c2"
    ACCENT_DEEP = "#173e41"
    WARNING = "#f7b955"
    DANGER = "#ff7a90"
    INPUT_BG = "#0f1727"
    INPUT_BORDER = "#314260"
    SELECT_BG = "#1f3558"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SQL Merge Tool")
        self.root.geometry("1240x860")
        self.root.minsize(1120, 760)

        self.project_root = Path(__file__).resolve().parents[2]
        self.sample_sql_dir = self.project_root / "sample_data" / "sample_sql"
        self.sample_spec_path = self.project_root / "sample_data" / "merge_spec.json"
        self.selected_sql_paths: list[Path] = []
        self.join_rows: list[dict[str, object]] = []
        self.join_field_state: dict[str, list[tuple[str, str]]] = {}
        self.sql_output_columns: dict[str, list[str]] = {}
        self.output_rows: list[dict[str, object]] = []
        self.output_column_state: dict[str, tuple[bool, str]] = {}
        self.output_column_order: list[str] = []
        self.last_merged_sql = ""

        self.main_sql_var = tk.StringVar()
        self.output_path_var = tk.StringVar(
            value=str(self.project_root / "merged_output.sql")
        )
        self.db_path_var = tk.StringVar(
            value=str(self.project_root / "sample_data" / "demo.sqlite")
        )
        self.status_var = tk.StringVar(value="尚未載入 SQL。")
        self.sql_count_var = tk.StringVar(value="0 files")

        self._configure_theme()
        self._build_layout()
        self._sync_sql_controls()

    def _configure_theme(self) -> None:
        """設定 dark mode 主題樣式。"""
        self.root.configure(bg=self.BG)

        default_font = ("Microsoft JhengHei UI", 10)
        heading_font = ("Microsoft JhengHei UI Semibold", 11)
        hero_font = ("Microsoft JhengHei UI Semibold", 22)
        mono_font = ("Consolas", 10)

        self.default_font = default_font
        self.heading_font = heading_font
        self.hero_font = hero_font
        self.mono_font = mono_font

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.BG, foreground=self.TEXT, font=default_font)
        style.configure("App.TFrame", background=self.BG)
        style.configure("Panel.TFrame", background=self.SURFACE)
        style.configure("Header.TFrame", background=self.SURFACE_ALT)
        style.configure("Card.TFrame", background=self.SURFACE)
        style.configure("CardInner.TFrame", background=self.PANEL)
        style.configure("App.TNotebook", background=self.BG, borderwidth=0, tabmargins=(0, 8, 0, 0))
        style.configure(
            "App.TNotebook.Tab",
            background=self.SURFACE_ALT,
            foreground=self.MUTED,
            padding=(18, 10),
            borderwidth=0,
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", self.SURFACE), ("active", "#20304d")],
            foreground=[("selected", self.TEXT), ("active", self.TEXT)],
        )

        style.configure(
            "Title.TLabel",
            background=self.SURFACE_ALT,
            foreground=self.TEXT,
            font=hero_font,
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.SURFACE_ALT,
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=heading_font,
        )
        style.configure(
            "Body.TLabel",
            background=self.SURFACE,
            foreground=self.MUTED,
        )
        style.configure(
            "Field.TLabel",
            background=self.PANEL,
            foreground=self.MUTED,
        )
        style.configure(
            "Status.TLabel",
            background=self.SURFACE_ALT,
            foreground=self.TEXT,
            font=("Microsoft JhengHei UI", 10),
        )
        style.configure(
            "Count.TLabel",
            background=self.SURFACE,
            foreground=self.ACCENT,
            font=("Consolas", 10, "bold"),
        )

        style.configure(
            "TEntry",
            fieldbackground=self.INPUT_BG,
            foreground=self.TEXT,
            bordercolor=self.INPUT_BORDER,
            lightcolor=self.INPUT_BORDER,
            darkcolor=self.INPUT_BORDER,
            insertcolor=self.TEXT,
            padding=8,
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", self.ACCENT)],
            lightcolor=[("focus", self.ACCENT)],
            darkcolor=[("focus", self.ACCENT)],
        )

        style.configure(
            "TCombobox",
            fieldbackground=self.INPUT_BG,
            foreground=self.TEXT,
            bordercolor=self.INPUT_BORDER,
            lightcolor=self.INPUT_BORDER,
            darkcolor=self.INPUT_BORDER,
            arrowsize=16,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.INPUT_BG)],
            foreground=[("readonly", self.TEXT)],
            bordercolor=[("focus", self.ACCENT)],
            lightcolor=[("focus", self.ACCENT)],
            darkcolor=[("focus", self.ACCENT)],
        )

        style.configure(
            "Accent.TButton",
            background=self.ACCENT,
            foreground="#071217",
            bordercolor=self.ACCENT,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
            padding=(14, 8),
            font=("Microsoft JhengHei UI Semibold", 10),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#73eed1"), ("pressed", "#3fc8ac")],
            foreground=[("disabled", "#34525e")],
        )

        style.configure(
            "Ghost.TButton",
            background=self.SURFACE_ALT,
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER,
            darkcolor=self.BORDER,
            padding=(12, 8),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#20304d"), ("pressed", "#18253c")],
        )

        style.configure(
            "Warn.TButton",
            background="#342515",
            foreground=self.WARNING,
            bordercolor="#5c4426",
            lightcolor="#5c4426",
            darkcolor="#5c4426",
            padding=(12, 8),
        )
        style.map(
            "Warn.TButton",
            background=[("active", "#48331d"), ("pressed", "#2e2113")],
        )

    def _build_layout(self) -> None:
        """建立 GUI 元件。"""
        outer = ttk.Frame(self.root, style="App.TFrame", padding=18)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        header = ttk.Frame(outer, style="Header.TFrame", padding=18)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="SQL Merge Console", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header,
            text="Dark mode GUI for WITH merge, main-table left join, and SQLite execution validation.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        toolbar = ttk.Frame(outer, style="App.TFrame", padding=(0, 14, 0, 10))
        toolbar.grid(row=1, column=0, sticky="ew")
        for column in range(8):
            toolbar.columnconfigure(column, weight=1)

        ttk.Button(
            toolbar,
            text="載入範例 SQL",
            command=self._load_sample_bundle,
            style="Ghost.TButton",
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ttk.Button(
            toolbar,
            text="加入 SQL 檔",
            command=self._select_sql_files,
            style="Accent.TButton",
        ).grid(row=0, column=1, padx=8, sticky="ew")
        ttk.Button(
            toolbar,
            text="載入規格 JSON",
            command=self._load_spec_file,
            style="Ghost.TButton",
        ).grid(row=0, column=2, padx=8, sticky="ew")
        ttk.Button(
            toolbar,
            text="儲存規格 JSON",
            command=self._save_spec_file,
            style="Ghost.TButton",
        ).grid(row=0, column=3, padx=8, sticky="ew")
        ttk.Button(
            toolbar,
            text="建立示範 SQLite",
            command=self._build_demo_database,
            style="Ghost.TButton",
        ).grid(row=0, column=4, padx=8, sticky="ew")
        ttk.Button(
            toolbar,
            text="讀取 SQL 欄位",
            command=self._load_sql_output_columns,
            style="Ghost.TButton",
        ).grid(row=0, column=5, padx=8, sticky="ew")
        ttk.Button(
            toolbar,
            text="產生合併 SQL",
            command=self._merge_sql,
            style="Accent.TButton",
        ).grid(row=0, column=6, padx=8, sticky="ew")
        ttk.Button(
            toolbar,
            text="驗證合併 SQL",
            command=self._validate_merged_sql,
            style="Warn.TButton",
        ).grid(row=0, column=7, padx=(8, 0), sticky="ew")

        notebook = ttk.Notebook(outer, style="App.TNotebook")
        notebook.grid(row=2, column=0, sticky="nsew", pady=(8, 0))

        workspace_tab = ttk.Frame(notebook, style="App.TFrame", padding=(0, 12, 0, 0))
        workspace_tab.columnconfigure(0, weight=1)
        workspace_tab.rowconfigure(1, weight=1)
        notebook.add(workspace_tab, text="工作區")

        output_tab = ttk.Frame(notebook, style="App.TFrame", padding=(0, 12, 0, 0))
        output_tab.columnconfigure(0, weight=1)
        output_tab.rowconfigure(0, weight=1)
        notebook.add(output_tab, text="輸出欄位")

        preview_tab = ttk.Frame(notebook, style="App.TFrame", padding=(0, 12, 0, 0))
        preview_tab.columnconfigure(0, weight=1)
        preview_tab.rowconfigure(0, weight=1)
        notebook.add(preview_tab, text="Merged SQL Preview")

        config_card = self._create_card(
            workspace_tab,
            row=0,
            title="執行設定",
            subtitle="主 SQL、輸出位置與 SQLite 驗證目標",
        )
        config_body = config_card["body"]
        config_body.columnconfigure(1, weight=1)

        ttk.Label(config_body, text="主 SQL", style="Field.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )
        self.main_sql_combo = ttk.Combobox(
            config_body,
            textvariable=self.main_sql_var,
            state="readonly",
            width=42,
        )
        self.main_sql_combo.grid(row=0, column=1, sticky="ew", pady=6)
        self.main_sql_combo.bind(
            "<<ComboboxSelected>>",
            lambda _: self._refresh_join_rows(),
        )

        ttk.Label(config_body, text="輸出 SQL", style="Field.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )
        ttk.Entry(config_body, textvariable=self.output_path_var).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=6,
        )

        ttk.Label(config_body, text="SQLite", style="Field.TLabel").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )
        ttk.Entry(config_body, textvariable=self.db_path_var).grid(
            row=2,
            column=1,
            sticky="ew",
            pady=6,
        )

        content = ttk.Frame(workspace_tab, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew", pady=(14, 14))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        sql_card = self._create_card(
            content,
            row=0,
            column=0,
            title="已選 SQL",
            subtitle="支援追加、刪除、清空，不必每次全部重選",
            padx=(0, 10),
            sticky="nsew",
        )
        sql_card["frame"].rowconfigure(1, weight=1)
        sql_body = sql_card["body"]
        sql_body.columnconfigure(0, weight=1)
        sql_body.rowconfigure(1, weight=1)

        top_row = ttk.Frame(sql_body, style="Panel.TFrame")
        top_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top_row.columnconfigure(0, weight=1)
        ttk.Label(top_row, textvariable=self.sql_count_var, style="Count.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )

        list_frame = tk.Frame(
            sql_body,
            bg=self.INPUT_BG,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.sql_listbox = tk.Listbox(
            list_frame,
            height=12,
            selectmode=tk.EXTENDED,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            selectbackground=self.SELECT_BG,
            selectforeground=self.TEXT,
            activestyle="none",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=self.default_font,
        )
        self.sql_listbox.grid(row=0, column=0, sticky="nsew")

        sql_scroll = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.sql_listbox.yview,
            bg=self.SURFACE_ALT,
            troughcolor=self.INPUT_BG,
            activebackground=self.ACCENT_DEEP,
            relief="flat",
        )
        sql_scroll.grid(row=0, column=1, sticky="ns")
        self.sql_listbox.configure(yscrollcommand=sql_scroll.set)

        sql_actions = ttk.Frame(sql_body, style="Panel.TFrame")
        sql_actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        sql_actions.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(
            sql_actions,
            text="加入",
            command=self._select_sql_files,
            style="Accent.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            sql_actions,
            text="刪除已選",
            command=self._remove_selected_sql_files,
            style="Ghost.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(
            sql_actions,
            text="清空",
            command=self._clear_selected_sql_files,
            style="Warn.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        join_card = self._create_card(
            content,
            row=0,
            column=1,
            title="Join 規格",
            subtitle="主表欄位對應右側 SQL 欄位，預設全部做 LEFT JOIN",
            padx=(10, 0),
            sticky="nsew",
        )
        join_card["frame"].rowconfigure(1, weight=1)
        join_body = join_card["body"]
        join_body.columnconfigure(0, weight=1)
        join_body.rowconfigure(1, weight=1)

        join_tip = ttk.Frame(join_body, style="Panel.TFrame")
        join_tip.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        join_tip.columnconfigure(0, weight=1)
        ttk.Label(
            join_tip,
            text="每支 SQL 可設定多組 key，最後會以 AND 組成 join 條件。",
            style="Body.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(
            join_tip,
            text="匯出 Excel",
            command=self._export_join_conditions_excel,
            style="Ghost.TButton",
        ).grid(row=0, column=1, padx=(8, 6), sticky="e")
        ttk.Button(
            join_tip,
            text="匯入 Excel",
            command=self._import_join_conditions_excel,
            style="Accent.TButton",
        ).grid(row=0, column=2, sticky="e")

        join_frame = tk.Frame(
            join_body,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        join_frame.grid(row=1, column=0, sticky="nsew")
        join_frame.grid_columnconfigure(0, weight=1)
        join_frame.grid_rowconfigure(0, weight=1)

        self.join_canvas = tk.Canvas(
            join_frame,
            bg=self.PANEL,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.join_canvas.grid(row=0, column=0, sticky="nsew")
        join_scroll = ttk.Scrollbar(
            join_frame,
            orient="vertical",
            command=self.join_canvas.yview,
        )
        join_scroll.grid(row=0, column=1, sticky="ns")
        self.join_canvas.configure(yscrollcommand=join_scroll.set)

        self.join_container = ttk.Frame(self.join_canvas, style="CardInner.TFrame", padding=12)
        self.join_window = self.join_canvas.create_window(
            (0, 0),
            window=self.join_container,
            anchor="nw",
        )
        self.join_container.bind("<Configure>", self._on_join_container_configure)
        self.join_canvas.bind("<Configure>", self._on_join_canvas_configure)

        output_card = self._create_card(
            output_tab,
            row=0,
            title="最終輸出欄位",
            subtitle="勾選要保留的欄位、調整順序，並設定 AS 中文名稱",
            sticky="nsew",
        )
        output_card["frame"].rowconfigure(1, weight=1)
        output_body = output_card["body"]
        output_body.columnconfigure(0, weight=1)
        output_body.rowconfigure(1, weight=1)

        output_tip = ttk.Frame(output_body, style="Panel.TFrame")
        output_tip.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        output_tip.columnconfigure(0, weight=1)
        ttk.Label(
            output_tip,
            text="先讀取 SQL 欄位，再在這裡決定最終欄位順序與中文欄名。",
            style="Body.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(
            output_tip,
            text="匯出 Excel",
            command=self._export_output_columns_excel,
            style="Ghost.TButton",
        ).grid(row=0, column=1, padx=(8, 6), sticky="e")
        ttk.Button(
            output_tip,
            text="匯入 Excel",
            command=self._import_output_columns_excel,
            style="Accent.TButton",
        ).grid(row=0, column=2, sticky="e")

        output_frame = tk.Frame(
            output_body,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        output_frame.grid(row=1, column=0, sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(0, weight=1)

        self.output_canvas = tk.Canvas(
            output_frame,
            bg=self.PANEL,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.output_canvas.grid(row=0, column=0, sticky="nsew")
        output_scroll = ttk.Scrollbar(
            output_frame,
            orient="vertical",
            command=self.output_canvas.yview,
        )
        output_scroll.grid(row=0, column=1, sticky="ns")
        self.output_canvas.configure(yscrollcommand=output_scroll.set)

        self.output_container = ttk.Frame(
            self.output_canvas,
            style="CardInner.TFrame",
            padding=12,
        )
        self.output_window = self.output_canvas.create_window(
            (0, 0),
            window=self.output_container,
            anchor="nw",
        )
        self.output_container.bind("<Configure>", self._on_output_container_configure)
        self.output_canvas.bind("<Configure>", self._on_output_canvas_configure)

        result_card = self._create_card(
            preview_tab,
            row=0,
            title="Merged SQL Preview",
            subtitle="直接預覽輸出結果，確認 WITH、CTE rename 與 LEFT JOIN 結構",
            sticky="nsew",
        )
        result_card["frame"].rowconfigure(1, weight=1)
        result_body = result_card["body"]
        result_body.columnconfigure(0, weight=1)
        result_body.rowconfigure(0, weight=1)

        editor_frame = tk.Frame(
            result_body,
            bg=self.INPUT_BG,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        editor_frame.grid(row=0, column=0, sticky="nsew")
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)

        self.result_text = tk.Text(
            editor_frame,
            wrap="none",
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground=self.SELECT_BG,
            selectforeground=self.TEXT,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=self.mono_font,
            padx=12,
            pady=12,
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        editor_scroll_y = tk.Scrollbar(
            editor_frame,
            orient="vertical",
            command=self.result_text.yview,
            bg=self.SURFACE_ALT,
            troughcolor=self.INPUT_BG,
            activebackground=self.ACCENT_DEEP,
            relief="flat",
        )
        editor_scroll_y.grid(row=0, column=1, sticky="ns")
        editor_scroll_x = tk.Scrollbar(
            editor_frame,
            orient="horizontal",
            command=self.result_text.xview,
            bg=self.SURFACE_ALT,
            troughcolor=self.INPUT_BG,
            activebackground=self.ACCENT_DEEP,
            relief="flat",
        )
        editor_scroll_x.grid(row=1, column=0, sticky="ew")
        self.result_text.configure(
            yscrollcommand=editor_scroll_y.set,
            xscrollcommand=editor_scroll_x.set,
        )

        status_bar = ttk.Frame(outer, style="Header.TFrame", padding=(14, 10))
        status_bar.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        status_bar.columnconfigure(0, weight=1)
        ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )

    def _create_card(
        self,
        parent: ttk.Frame,
        row: int,
        title: str,
        subtitle: str,
        column: int = 0,
        padx: tuple[int, int] = (0, 0),
        sticky: str = "ew",
    ) -> dict[str, ttk.Frame]:
        """建立帶標題的卡片區塊。"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        card.grid(row=row, column=column, sticky=sticky, padx=padx)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        ttk.Label(card, text=title, style="Section.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(card, text=subtitle, style="Body.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 12),
        )

        body = ttk.Frame(card, style="CardInner.TFrame", padding=14)
        body.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(2, weight=1)
        return {"frame": card, "body": body}

    def _select_sql_files(self) -> None:
        """讓使用者手動追加多個 SQL。"""
        paths = filedialog.askopenfilenames(
            title="選取要合併的 SQL",
            filetypes=[("SQL files", "*.sql")],
            initialdir=self.project_root,
        )
        if not paths:
            return
        existing_paths = {path.resolve(): path for path in self.selected_sql_paths}
        for raw_path in paths:
            path = Path(raw_path)
            existing_paths[path.resolve()] = path
        self.selected_sql_paths = sorted(
            existing_paths.values(),
            key=lambda item: item.name.lower(),
        )
        self._sync_sql_controls()
        self._try_auto_load_sql_output_columns()
        self.status_var.set("已加入 SQL 到清單。")

    def _load_sample_bundle(self) -> None:
        """載入內建範例 SQL 與規格。"""
        self.selected_sql_paths = sorted(self.sample_sql_dir.glob("*.sql"))
        self.join_field_state.clear()
        self.output_column_state.clear()
        self.output_column_order.clear()
        self._sync_sql_controls()
        if self.sample_spec_path.exists():
            spec = load_merge_spec(self.sample_spec_path)
            self._apply_spec(spec)
        self._try_auto_load_sql_output_columns()
        self.status_var.set("已載入範例 SQL 與預設 join 規格。")

    def _remove_selected_sql_files(self) -> None:
        """從清單中移除目前選取的 SQL。"""
        selected_indexes = list(self.sql_listbox.curselection())
        if not selected_indexes:
            self.status_var.set("請先在已選 SQL 清單中選取要刪除的檔案。")
            return

        self._capture_join_field_state()
        selected_names = {str(self.sql_listbox.get(index)) for index in selected_indexes}
        self.selected_sql_paths = [
            path for path in self.selected_sql_paths if path.name not in selected_names
        ]
        for file_name in selected_names:
            self.join_field_state.pop(file_name, None)
            self.sql_output_columns.pop(file_name, None)
        self.output_column_order = [
            key
            for key in self.output_column_order
            if self._parse_output_key(key)[0] not in selected_names
        ]
        self.output_column_state = {
            key: value
            for key, value in self.output_column_state.items()
            if self._parse_output_key(key)[0] not in selected_names
        }
        self._sync_sql_controls()
        self.status_var.set(f"已刪除 {len(selected_names)} 個 SQL。")

    def _clear_selected_sql_files(self) -> None:
        """清空目前已選 SQL。"""
        self.selected_sql_paths = []
        self.join_field_state.clear()
        self.sql_output_columns.clear()
        self.output_column_state.clear()
        self.output_column_order.clear()
        self._sync_sql_controls()
        self.status_var.set("已清空 SQL 清單。")

    def _sync_sql_controls(self) -> None:
        """同步已選 SQL 清單與主 SQL 下拉選單。"""
        self._capture_join_field_state()
        file_names = [path.name for path in self.selected_sql_paths]
        self.sql_count_var.set(f"{len(file_names)} files")

        self.sql_listbox.delete(0, tk.END)
        for file_name in file_names:
            self.sql_listbox.insert(tk.END, file_name)

        self.main_sql_combo["values"] = file_names
        if file_names:
            current_value = self.main_sql_var.get()
            if current_value not in file_names:
                self.main_sql_var.set(self._choose_default_main_sql(file_names))
        else:
            self.main_sql_var.set("")

        self._refresh_join_rows()
        self._sync_output_column_catalog()

    def _refresh_join_rows(self) -> None:
        """依目前主 SQL 重建 join 設定列。"""
        for widget in self.join_container.winfo_children():
            widget.destroy()
        self.join_rows.clear()

        ttk.Label(self.join_container, text="Join SQL", style="Field.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=4,
            pady=(0, 10),
        )
        ttk.Label(self.join_container, text="主表欄位", style="Field.TLabel").grid(
            row=0,
            column=1,
            sticky="w",
            padx=4,
            pady=(0, 10),
        )
        ttk.Label(self.join_container, text="對應欄位", style="Field.TLabel").grid(
            row=0,
            column=2,
            sticky="w",
            padx=4,
            pady=(0, 10),
        )
        ttk.Label(self.join_container, text="操作", style="Field.TLabel").grid(
            row=0,
            column=3,
            sticky="w",
            padx=4,
            pady=(0, 10),
        )

        main_sql = self.main_sql_var.get()
        main_columns = self.sql_output_columns.get(main_sql, [])
        row_index = 1
        for path in self.selected_sql_paths:
            if path.name == main_sql:
                continue
            saved_conditions = self._resolve_join_defaults(
                sql_file=path.name,
                main_columns=main_columns,
                other_columns=self.sql_output_columns.get(path.name, []),
            )
            other_columns = self.sql_output_columns.get(path.name, [])

            row_frame = tk.Frame(
                self.join_container,
                bg=self.SURFACE_ALT if row_index % 2 else self.PANEL,
                highlightbackground=self.BORDER,
                highlightthickness=1,
                bd=0,
            )
            row_frame.grid(row=row_index, column=0, columnspan=4, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(0, weight=1)

            tk.Label(
                row_frame,
                text=path.name,
                bg=row_frame["bg"],
                fg=self.TEXT,
                anchor="w",
                padx=10,
                pady=10,
                font=self.default_font,
            ).grid(row=0, column=0, sticky="w")

            add_button = ttk.Button(
                row_frame,
                text="+ 新增 Key",
                style="Ghost.TButton",
                command=lambda sql_file=path.name: self._add_join_condition(sql_file),
            )
            add_button.grid(row=0, column=1, sticky="e", padx=10, pady=(8, 4))

            condition_container = ttk.Frame(row_frame, style="Panel.TFrame")
            condition_container.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
            condition_container.columnconfigure(0, weight=1)
            condition_container.columnconfigure(1, weight=1)

            condition_rows = []
            for condition_index, (saved_main_column, saved_other_column) in enumerate(saved_conditions):
                main_column_var = tk.StringVar(value=saved_main_column)
                other_column_var = tk.StringVar(value=saved_other_column)

                main_combo = ttk.Combobox(
                    condition_container,
                    textvariable=main_column_var,
                    values=self._build_column_values(main_columns, saved_main_column),
                    state="normal",
                )
                main_combo.grid(row=condition_index, column=0, sticky="ew", padx=(0, 8), pady=4)

                other_combo = ttk.Combobox(
                    condition_container,
                    textvariable=other_column_var,
                    values=self._build_column_values(other_columns, saved_other_column),
                    state="normal",
                )
                other_combo.grid(row=condition_index, column=1, sticky="ew", padx=(0, 8), pady=4)

                remove_button = ttk.Button(
                    condition_container,
                    text="刪除",
                    style="Warn.TButton",
                    command=lambda sql_file=path.name, row_idx=condition_index: self._remove_join_condition(sql_file, row_idx),
                )
                remove_button.grid(row=condition_index, column=2, sticky="ew", pady=4)

                condition_rows.append(
                    {
                        "main_column_var": main_column_var,
                        "other_column_var": other_column_var,
                    }
                )

            self.join_rows.append(
                {
                    "sql_file": path.name,
                    "condition_rows": condition_rows,
                }
            )
            row_index += 1

        self.join_canvas.update_idletasks()
        self.join_canvas.configure(scrollregion=self.join_canvas.bbox("all"))

    def _capture_join_field_state(self) -> None:
        """在重建畫面前，保留目前 join 欄位設定。"""
        for row in self.join_rows:
            sql_file = str(row["sql_file"])
            conditions = []
            for condition_row in row["condition_rows"]:
                main_column = str(condition_row["main_column_var"].get()).strip()
                other_column = str(condition_row["other_column_var"].get()).strip()
                if main_column or other_column:
                    conditions.append((main_column, other_column))
            self.join_field_state[sql_file] = conditions or [("", "")]

    def _add_join_condition(self, sql_file: str) -> None:
        """為指定 SQL 新增一組 join key。"""
        self._capture_join_field_state()
        conditions = list(self.join_field_state.get(sql_file, [("", "")]))
        conditions.append(("", ""))
        self.join_field_state[sql_file] = conditions
        self._refresh_join_rows()

    def _remove_join_condition(self, sql_file: str, row_index: int) -> None:
        """移除指定 SQL 的一組 join key。"""
        self._capture_join_field_state()
        conditions = list(self.join_field_state.get(sql_file, [("", "")]))
        if len(conditions) <= 1:
            return
        if 0 <= row_index < len(conditions):
            conditions.pop(row_index)
        self.join_field_state[sql_file] = conditions or [("", "")]
        self._refresh_join_rows()

    def _build_join_condition_excel_rows(self) -> list[JoinConditionExcelRow]:
        """依目前 join 設定建立 Excel 資料列。"""
        self._capture_join_field_state()
        rows: list[JoinConditionExcelRow] = []
        for sql_file in self._build_output_source_order():
            if sql_file == self.main_sql_var.get().strip():
                continue
            conditions = self.join_field_state.get(sql_file, [("", "")])
            for key_order, (main_column, other_column) in enumerate(conditions, start=1):
                if not main_column and not other_column:
                    continue
                rows.append(
                    JoinConditionExcelRow(
                        sql_file=sql_file,
                        key_order=key_order,
                        main_column=main_column,
                        other_column=other_column,
                    )
                )
        return rows

    def _export_join_conditions_excel(self) -> None:
        """將目前 join 多 key 設定匯出成 Excel。"""
        rows = self._build_join_condition_excel_rows()
        if not rows:
            messagebox.showerror(
                "匯出失敗",
                "目前沒有可匯出的 join 規格。請先設定 join key。",
            )
            return

        path = filedialog.asksaveasfilename(
            title="匯出 Join 規格 Excel",
            filetypes=[("Excel files", "*.xlsx")],
            defaultextension=".xlsx",
            initialdir=self.project_root,
            initialfile="join_conditions.xlsx",
        )
        if not path:
            return

        export_join_conditions_to_excel(Path(path), rows)
        self.status_var.set(f"已匯出 Join 規格 Excel: {path}")

    def _import_join_conditions_excel(self) -> None:
        """從 Excel 匯入 join 多 key 設定。"""
        if not self.selected_sql_paths:
            messagebox.showerror("匯入失敗", "目前沒有可套用的 SQL。")
            return

        path = filedialog.askopenfilename(
            title="匯入 Join 規格 Excel",
            filetypes=[("Excel files", "*.xlsx")],
            initialdir=self.project_root,
        )
        if not path:
            return

        imported_rows = import_join_conditions_from_excel(Path(path))
        if not imported_rows:
            messagebox.showerror("匯入失敗", "Excel 內沒有可用的 join 規格。")
            return

        main_sql = self.main_sql_var.get().strip()
        valid_sql_files = {
            path.name for path in self.selected_sql_paths if path.name != main_sql
        }
        imported_state: dict[str, list[tuple[str, str]]] = {}
        skipped_rows: list[str] = []

        for row in imported_rows:
            if row.sql_file not in valid_sql_files:
                skipped_rows.append(f"{row.sql_file} (不存在或為主 SQL)")
                continue
            imported_state.setdefault(row.sql_file, []).append(
                (row.main_column, row.other_column)
            )

        if not imported_state:
            messagebox.showerror("匯入失敗", "Excel 內容與目前 join SQL 清單對不上。")
            return

        self._capture_join_field_state()
        for sql_file, conditions in imported_state.items():
            self.join_field_state[sql_file] = conditions or [("", "")]
        self._refresh_join_rows()

        if skipped_rows:
            messagebox.showwarning(
                "部分 Join 已略過",
                "以下資料列未套用：\n" + "\n".join(sorted(set(skipped_rows))),
            )

        self.status_var.set(f"已匯入 Join 規格 Excel: {path}")

    def _capture_output_column_state(self) -> None:
        """在重建輸出欄位畫面前，保留目前勾選、別名與順序。"""
        order: list[str] = []
        for row in self.output_rows:
            key = str(row["key"])
            enabled = bool(row["enabled_var"].get())
            display_name = str(row["display_name_var"].get()).strip()
            self.output_column_state[key] = (enabled, display_name)
            order.append(key)
        if order:
            self.output_column_order = order

    def _make_output_key(self, source_sql: str, column_name: str) -> str:
        """建立輸出欄位唯一鍵值。"""
        return f"{source_sql}::{column_name}"

    def _parse_output_key(self, key: str) -> tuple[str, str]:
        """還原輸出欄位鍵值。"""
        source_sql, column_name = key.split("::", 1)
        return source_sql, column_name

    def _build_output_source_order(self) -> list[str]:
        """依主 SQL 與 joins 順序建立輸出來源順序。"""
        main_sql = self.main_sql_var.get().strip()
        ordered_sources = []
        if main_sql:
            ordered_sources.append(main_sql)
        ordered_sources.extend(
            path.name for path in self.selected_sql_paths if path.name != main_sql
        )
        return ordered_sources

    def _sync_output_column_catalog(self) -> None:
        """同步輸出欄位清單、順序與目前狀態。"""
        self._capture_output_column_state()

        if not self.selected_sql_paths:
            self.output_column_state.clear()
            self.output_column_order.clear()
            self._refresh_output_rows()
            return

        if not self.sql_output_columns:
            self._refresh_output_rows()
            return

        default_order: list[str] = []
        for source_sql in self._build_output_source_order():
            for column_name in self.sql_output_columns.get(source_sql, []):
                key = self._make_output_key(source_sql, column_name)
                default_order.append(key)
                self.output_column_state.setdefault(key, (True, ""))

        valid_keys = set(default_order)
        self.output_column_state = {
            key: value
            for key, value in self.output_column_state.items()
            if key in valid_keys
        }

        ordered_keys = [
            key for key in self.output_column_order if key in valid_keys
        ]
        for key in default_order:
            if key not in ordered_keys:
                ordered_keys.append(key)
        self.output_column_order = ordered_keys
        self._refresh_output_rows()

    def _refresh_output_rows(self) -> None:
        """重建輸出欄位設定畫面。"""
        for widget in self.output_container.winfo_children():
            widget.destroy()
        self.output_rows.clear()

        if not self.output_column_order:
            ttk.Label(
                self.output_container,
                text="尚未讀到 SQL 輸出欄位。先建立 SQLite，再按「讀取 SQL 欄位」。",
                style="Body.TLabel",
            ).grid(row=0, column=0, sticky="w")
            self.output_canvas.update_idletasks()
            self.output_canvas.configure(scrollregion=self.output_canvas.bbox("all"))
            return

        headers = ["啟用", "#", "來源 SQL", "原始欄位", "中文 AS", "排序"]
        for column_index, header_text in enumerate(headers):
            ttk.Label(
                self.output_container,
                text=header_text,
                style="Field.TLabel",
            ).grid(row=0, column=column_index, sticky="w", padx=4, pady=(0, 10))

        self.output_container.columnconfigure(4, weight=1)

        for row_index, key in enumerate(self.output_column_order, start=1):
            source_sql, column_name = self._parse_output_key(key)
            enabled, display_name = self.output_column_state.get(key, (True, ""))
            enabled_var = tk.BooleanVar(value=enabled)
            display_name_var = tk.StringVar(value=display_name)

            row_frame = tk.Frame(
                self.output_container,
                bg=self.SURFACE_ALT if row_index % 2 else self.PANEL,
                highlightbackground=self.BORDER,
                highlightthickness=1,
                bd=0,
            )
            row_frame.grid(row=row_index, column=0, columnspan=6, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(4, weight=1)

            enabled_check = tk.Checkbutton(
                row_frame,
                variable=enabled_var,
                onvalue=True,
                offvalue=False,
                bg=row_frame["bg"],
                activebackground=row_frame["bg"],
                fg=self.TEXT,
                selectcolor=self.INPUT_BG,
                highlightthickness=0,
                bd=0,
            )
            enabled_check.grid(row=0, column=0, padx=(8, 6), pady=8)

            tk.Label(
                row_frame,
                text=str(row_index),
                bg=row_frame["bg"],
                fg=self.ACCENT,
                width=4,
                anchor="w",
                font=self.default_font,
            ).grid(row=0, column=1, sticky="w", padx=(0, 8))
            tk.Label(
                row_frame,
                text=source_sql,
                bg=row_frame["bg"],
                fg=self.TEXT,
                anchor="w",
                width=22,
                font=self.default_font,
            ).grid(row=0, column=2, sticky="w", padx=(0, 8))
            tk.Label(
                row_frame,
                text=column_name,
                bg=row_frame["bg"],
                fg=self.MUTED,
                anchor="w",
                width=22,
                font=self.default_font,
            ).grid(row=0, column=3, sticky="w", padx=(0, 8))

            alias_entry = ttk.Entry(row_frame, textvariable=display_name_var)
            alias_entry.grid(row=0, column=4, sticky="ew", padx=(0, 8), pady=8)

            action_frame = ttk.Frame(row_frame, style="Panel.TFrame")
            action_frame.grid(row=0, column=5, sticky="e", padx=(0, 8))
            ttk.Button(
                action_frame,
                text="↑",
                width=3,
                style="Ghost.TButton",
                command=lambda key=key: self._move_output_row(key, -1),
            ).pack(side="left", padx=(0, 4))
            ttk.Button(
                action_frame,
                text="↓",
                width=3,
                style="Ghost.TButton",
                command=lambda key=key: self._move_output_row(key, 1),
            ).pack(side="left")

            self.output_rows.append(
                {
                    "key": key,
                    "enabled_var": enabled_var,
                    "display_name_var": display_name_var,
                }
            )

        self.output_canvas.update_idletasks()
        self.output_canvas.configure(scrollregion=self.output_canvas.bbox("all"))

    def _move_output_row(self, key: str, direction: int) -> None:
        """調整輸出欄位順序。"""
        self._capture_output_column_state()
        try:
            index = self.output_column_order.index(key)
        except ValueError:
            return
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.output_column_order):
            return
        self.output_column_order[index], self.output_column_order[new_index] = (
            self.output_column_order[new_index],
            self.output_column_order[index],
        )
        self._refresh_output_rows()

    def _build_output_excel_rows(self) -> list[OutputColumnExcelRow]:
        """依目前輸出欄位設定建立 Excel 資料列。"""
        self._capture_output_column_state()
        rows: list[OutputColumnExcelRow] = []
        for order, key in enumerate(self.output_column_order, start=1):
            source_sql, column_name = self._parse_output_key(key)
            enabled, display_name = self.output_column_state.get(key, (True, ""))
            rows.append(
                OutputColumnExcelRow(
                    source_sql=source_sql,
                    column_name=column_name,
                    enabled=enabled,
                    display_name=display_name,
                    order=order,
                )
            )
        return rows

    def _export_output_columns_excel(self) -> None:
        """將目前輸出欄位設定匯出成 Excel。"""
        if not self.output_column_order:
            messagebox.showerror(
                "匯出失敗",
                "目前沒有可匯出的輸出欄位。請先讀取 SQL 欄位。",
            )
            return

        path = filedialog.asksaveasfilename(
            title="匯出輸出欄位 Excel",
            filetypes=[("Excel files", "*.xlsx")],
            defaultextension=".xlsx",
            initialdir=self.project_root,
            initialfile="output_columns.xlsx",
        )
        if not path:
            return

        export_output_columns_to_excel(Path(path), self._build_output_excel_rows())
        self.status_var.set(f"已匯出輸出欄位 Excel: {path}")

    def _import_output_columns_excel(self) -> None:
        """從 Excel 匯入輸出欄位設定並更新順序。"""
        if not self.sql_output_columns:
            messagebox.showerror(
                "匯入失敗",
                "請先建立 SQLite 並讀取 SQL 欄位，之後再匯入 Excel。",
            )
            return

        path = filedialog.askopenfilename(
            title="匯入輸出欄位 Excel",
            filetypes=[("Excel files", "*.xlsx")],
            initialdir=self.project_root,
        )
        if not path:
            return

        imported_rows = import_output_columns_from_excel(Path(path))
        if not imported_rows:
            messagebox.showerror("匯入失敗", "Excel 內沒有可用的輸出欄位設定。")
            return

        valid_keys = {
            self._make_output_key(source_sql, column_name)
            for source_sql, columns in self.sql_output_columns.items()
            for column_name in columns
        }
        new_state: dict[str, tuple[bool, str]] = {}
        new_order: list[str] = []
        skipped_rows: list[str] = []

        for row in imported_rows:
            key = self._make_output_key(row.source_sql, row.column_name)
            if key not in valid_keys:
                skipped_rows.append(f"{row.source_sql}.{row.column_name}")
                continue
            new_state[key] = (row.enabled, row.display_name)
            new_order.append(key)

        if not new_order:
            messagebox.showerror("匯入失敗", "Excel 內容與目前 SQL 欄位對不上。")
            return

        for key, value in self.output_column_state.items():
            if key not in new_state and key in valid_keys:
                new_state[key] = value
        for key in self.output_column_order:
            if key not in new_order and key in valid_keys:
                new_order.append(key)
        for key in sorted(valid_keys):
            if key not in new_order:
                new_order.append(key)

        self.output_column_state = new_state
        self.output_column_order = new_order
        self._refresh_output_rows()

        if skipped_rows:
            messagebox.showwarning(
                "部分欄位已略過",
                "以下欄位不在目前 SQL 清單中，已跳過：\n" + "\n".join(skipped_rows),
            )

        self.status_var.set(f"已匯入輸出欄位 Excel: {path}")

    def _build_column_values(self, columns: list[str], current_value: str) -> list[str]:
        """建立下拉選單欄位值，保留當前手動輸入。"""
        values = list(columns)
        if current_value and current_value not in values:
            values.append(current_value)
        return values

    def _choose_default_main_sql(self, file_names: list[str]) -> str:
        """優先挑選名稱看起來像主表的 SQL。"""
        for name in file_names:
            lowered = name.lower()
            if lowered.endswith("_main.sql") or lowered.startswith("main_"):
                return name
            if "main" in lowered:
                return name
        return file_names[0]

    def _suggest_join_columns(
        self,
        main_columns: list[str],
        other_columns: list[str],
    ) -> tuple[str, str]:
        """依輸出欄位嘗試找出合理的 join 欄位。"""
        shared_columns = [column for column in main_columns if column in other_columns]
        if shared_columns:
            return shared_columns[0], shared_columns[0]
        return "", ""

    def _resolve_join_defaults(
        self,
        sql_file: str,
        main_columns: list[str],
        other_columns: list[str],
    ) -> list[tuple[str, str]]:
        """若舊設定已不適用目前主 SQL，則改用欄位建議值。"""
        saved_conditions = self.join_field_state.get(sql_file, [("", "")])
        valid_conditions = [
            (main_column, other_column)
            for main_column, other_column in saved_conditions
            if (
                main_column
                and other_column
                and (not main_columns or main_column in main_columns)
                and (not other_columns or other_column in other_columns)
            )
        ]
        if valid_conditions:
            return valid_conditions

        suggested_main, suggested_other = self._suggest_join_columns(main_columns, other_columns)
        if suggested_main or suggested_other:
            return [(suggested_main, suggested_other)]
        return [("", "")]

    def _validate_join_columns(self) -> None:
        """在合併前先檢查目前主 SQL 與 join 欄位是否合理。"""
        if not self.sql_output_columns:
            return

        main_sql = self.main_sql_var.get().strip()
        main_columns = set(self.sql_output_columns.get(main_sql, []))
        if not main_columns:
            return

        for row in self.join_rows:
            sql_file = str(row["sql_file"])
            other_columns = set(self.sql_output_columns.get(sql_file, []))
            condition_rows = row["condition_rows"]
            if not condition_rows:
                raise ValueError(f"{sql_file} 尚未設定 join key。")

            for condition_index, condition_row in enumerate(condition_rows, start=1):
                main_column = str(condition_row["main_column_var"].get()).strip()
                other_column = str(condition_row["other_column_var"].get()).strip()

                if not main_column or not other_column:
                    raise ValueError(
                        f"{sql_file} 第 {condition_index} 組 join key 尚未選定。"
                    )
                if main_column not in main_columns:
                    raise ValueError(
                        f"主 SQL {main_sql} 沒有欄位 {main_column}。"
                    )
                if other_columns and other_column not in other_columns:
                    raise ValueError(
                        f"{sql_file} 沒有欄位 {other_column}。"
                    )

    def _try_auto_load_sql_output_columns(self) -> None:
        """若 SQLite 已存在，則自動讀取 SQL 輸出欄位。"""
        db_path = Path(self.db_path_var.get())
        if db_path.exists() and self.selected_sql_paths:
            self._load_sql_output_columns(silent=True)

    def _load_sql_output_columns(self, silent: bool = False) -> None:
        """讀取每支 .sql 最終輸出的欄位。"""
        if not self.selected_sql_paths:
            if not silent:
                messagebox.showerror("讀取失敗", "目前沒有可讀取欄位的 SQL。")
            return

        db_path = Path(self.db_path_var.get())
        if not db_path.exists():
            if not silent:
                messagebox.showerror("讀取失敗", f"找不到 SQLite:\n{db_path}")
            return

        column_map: dict[str, list[str]] = {}
        errors: list[str] = []
        for sql_path in self.selected_sql_paths:
            try:
                column_map[sql_path.name] = describe_sql_file_columns(db_path, sql_path)
            except Exception as error:  # noqa: BLE001
                errors.append(f"{sql_path.name}: {error}")

        if column_map:
            self._capture_join_field_state()
            self.sql_output_columns = column_map
            self._refresh_join_rows()
            self._sync_output_column_catalog()

        if errors and not silent:
            messagebox.showwarning(
                "部分欄位讀取失敗",
                "以下 SQL 無法讀取輸出欄位：\n" + "\n".join(errors),
            )

        if column_map:
            self.status_var.set(f"已讀取 {len(column_map)} 支 SQL 的輸出欄位。")
        elif errors and not silent:
            self.status_var.set("SQL 輸出欄位讀取失敗。")

    def _on_join_container_configure(self, _: tk.Event) -> None:
        """同步 join canvas 捲動範圍。"""
        self.join_canvas.configure(scrollregion=self.join_canvas.bbox("all"))

    def _on_join_canvas_configure(self, event: tk.Event) -> None:
        """讓 join 內容寬度跟著外層卡片變動。"""
        self.join_canvas.itemconfigure(self.join_window, width=event.width)

    def _on_output_container_configure(self, _: tk.Event) -> None:
        """同步輸出欄位 canvas 捲動範圍。"""
        self.output_canvas.configure(scrollregion=self.output_canvas.bbox("all"))

    def _on_output_canvas_configure(self, event: tk.Event) -> None:
        """讓輸出欄位內容寬度跟著外層卡片變動。"""
        self.output_canvas.itemconfigure(self.output_window, width=event.width)

    def _build_spec_from_form(self) -> MergeSpec:
        """將 GUI 畫面轉成 MergeSpec。"""
        main_sql = self.main_sql_var.get().strip()
        if not main_sql:
            raise ValueError("請先選擇主 SQL。")

        self._capture_output_column_state()
        joins = []
        for row in self.join_rows:
            sql_file = str(row["sql_file"])
            conditions = []
            for condition_row in row["condition_rows"]:
                main_column = str(condition_row["main_column_var"].get()).strip()
                other_column = str(condition_row["other_column_var"].get()).strip()
                conditions.append(
                    JoinCondition(
                        main_column=main_column,
                        other_column=other_column,
                    )
                )
            joins.append(
                JoinSpec(
                    sql_file=sql_file,
                    join_type="LEFT",
                    conditions=conditions,
                )
            )

        output_columns = []
        for key in self.output_column_order:
            source_sql, column_name = self._parse_output_key(key)
            enabled, display_name = self.output_column_state.get(key, (True, ""))
            output_columns.append(
                OutputColumnSpec(
                    source_sql=source_sql,
                    column_name=column_name,
                    enabled=enabled,
                    display_name=display_name,
                )
            )

        return MergeSpec(
            main_sql=main_sql,
            joins=joins,
            output_columns=output_columns,
        )

    def _apply_spec(self, spec: MergeSpec) -> None:
        """把載入的規格回填到畫面。"""
        if spec.main_sql:
            self.main_sql_var.set(spec.main_sql)
        self.join_field_state = {
            join.sql_file: [
                (condition.main_column, condition.other_column)
                for condition in join.conditions
            ]
            or [("", "")]
            for join in spec.joins
        }
        self._refresh_join_rows()

        self._capture_join_field_state()
        if spec.output_columns:
            self.output_column_state = {
                self._make_output_key(column.source_sql, column.column_name): (
                    column.enabled,
                    column.display_name,
                )
                for column in spec.output_columns
            }
            self.output_column_order = [
                self._make_output_key(column.source_sql, column.column_name)
                for column in spec.output_columns
            ]
        if self.sql_output_columns:
            self._sync_output_column_catalog()
        else:
            self._refresh_output_rows()

    def _load_spec_file(self) -> None:
        """從檔案載入規格。"""
        path = filedialog.askopenfilename(
            title="選取 merge spec JSON",
            filetypes=[("JSON files", "*.json")],
            initialdir=self.project_root,
        )
        if not path:
            return
        spec = load_merge_spec(Path(path))
        self._apply_spec(spec)
        self.status_var.set(f"已載入規格: {path}")

    def _save_spec_file(self) -> None:
        """把目前畫面設定另存成 JSON。"""
        try:
            spec = self._build_spec_from_form()
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("規格錯誤", str(error))
            return

        path = filedialog.asksaveasfilename(
            title="儲存 merge spec JSON",
            filetypes=[("JSON files", "*.json")],
            defaultextension=".json",
            initialdir=self.project_root,
        )
        if not path:
            return
        save_merge_spec(Path(path), spec)
        self.status_var.set(f"已儲存規格: {path}")

    def _build_demo_database(self) -> None:
        """建立示範 SQLite 檔案。"""
        db_path = Path(self.db_path_var.get())
        seed_demo_database(db_path)
        self._load_sql_output_columns(silent=True)
        self.status_var.set(f"已建立 SQLite: {db_path}")
        messagebox.showinfo("完成", f"已建立示範 SQLite:\n{db_path}")

    def _merge_sql(self) -> None:
        """執行 SQL 合併並輸出檔案。"""
        try:
            self._validate_join_columns()
            spec = self._build_spec_from_form()
            merged_sql = merge_sql_files(self.selected_sql_paths, spec)
            output_path = Path(self.output_path_var.get())
            save_merged_sql(output_path, merged_sql)
            self.last_merged_sql = merged_sql
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", merged_sql)
            self.status_var.set(f"已輸出合併 SQL: {output_path}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("合併失敗", str(error))

    def _validate_merged_sql(self) -> None:
        """對 SQLite 實際執行合併 SQL。"""
        try:
            if not self.last_merged_sql.strip():
                self._merge_sql()
            db_path = Path(self.db_path_var.get())
            if not db_path.exists():
                seed_demo_database(db_path)
            columns, rows = execute_sql(db_path, self.last_merged_sql)
            self.status_var.set(
                f"驗證完成，欄位數 {len(columns)}，資料筆數 {len(rows)}。"
            )
            messagebox.showinfo(
                "驗證完成",
                f"SQLite 執行成功。\n欄位數: {len(columns)}\n資料筆數: {len(rows)}",
            )
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("驗證失敗", str(error))


def launch_app() -> None:
    """啟動 GUI。"""
    configure_logging()
    root = tk.Tk()
    SqlMergeApp(root)
    root.mainloop()
