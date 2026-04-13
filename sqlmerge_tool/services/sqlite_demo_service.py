"""建立與驗證 SQLite 示範資料。"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS risks;
DROP TABLE IF EXISTS policy_changes;
DROP TABLE IF EXISTS policies;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE policies (
    policy_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    policy_number TEXT NOT NULL,
    status TEXT NOT NULL,
    premium REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE policy_changes (
    change_id INTEGER PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    change_date TEXT NOT NULL,
    change_type TEXT NOT NULL,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE TABLE risks (
    risk_id INTEGER PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    risk_code TEXT NOT NULL,
    risk_level INTEGER NOT NULL,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE TABLE claims (
    claim_id INTEGER PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    claim_date TEXT NOT NULL,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);
"""


def seed_demo_database(db_path: Path) -> Path:
    """建立 5 張 table 並塞入可驗證的示範資料。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_SQL)
        connection.executemany(
            "INSERT INTO customers (customer_id, customer_name, city) VALUES (?, ?, ?)",
            [
                (1, "王小明", "Taipei"),
                (2, "陳美玲", "Taichung"),
                (3, "林大華", "Tainan"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO policies (
                policy_id,
                customer_id,
                policy_number,
                status,
                premium
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (101, 1, "P-001", "ACTIVE", 12000.0),
                (102, 2, "P-002", "ACTIVE", 18000.0),
                (103, 3, "P-003", "LAPSED", 9000.0),
            ],
        )
        connection.executemany(
            """
            INSERT INTO policy_changes (
                change_id,
                policy_id,
                change_date,
                change_type
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (1, 101, "2026-01-05", "ADDRESS"),
                (2, 101, "2026-03-01", "BENEFICIARY"),
                (3, 102, "2026-02-10", "PAYMENT"),
                (4, 103, "2026-01-20", "STATUS"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO risks (
                risk_id,
                policy_id,
                risk_code,
                risk_level
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (1, 101, "RISK-A", 2),
                (2, 101, "RISK-B", 4),
                (3, 102, "RISK-C", 3),
            ],
        )
        connection.executemany(
            """
            INSERT INTO claims (
                claim_id,
                policy_id,
                amount,
                claim_date
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (1, 101, 5000.0, "2026-03-10"),
                (2, 102, 1000.0, "2026-02-18"),
                (3, 102, 2000.0, "2026-03-22"),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def execute_sql(db_path: Path, sql_text: str) -> tuple[list[str], list[sqlite3.Row]]:
    """執行 SQL 並回傳欄位名稱與資料列。"""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.execute(sql_text)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description or []]
        return columns, rows
    finally:
        connection.close()


def execute_sql_file(db_path: Path, sql_path: Path) -> tuple[list[str], list[sqlite3.Row]]:
    """直接執行 .sql 檔案。"""
    return execute_sql(db_path, sql_path.read_text(encoding="utf-8"))


def describe_sql_columns(db_path: Path, sql_text: str) -> list[str]:
    """讀取 SQL 最終輸出的欄位名稱，而不是底層 table schema。"""
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(sql_text.strip().rstrip(";"))
        return [column[0] for column in cursor.description or []]
    finally:
        connection.close()


def describe_sql_file_columns(db_path: Path, sql_path: Path) -> list[str]:
    """直接讀取 .sql 檔的輸出欄位名稱。"""
    return describe_sql_columns(db_path, sql_path.read_text(encoding="utf-8"))
