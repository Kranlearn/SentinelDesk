from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


DEFAULT_DATABASE = Path(__file__).with_name("sentineldesk.db")


def connect(database: str | Path = DEFAULT_DATABASE) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database(database: str | Path = DEFAULT_DATABASE) -> None:
    with closing(connect(database)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity)"
        )


def save_event(database: str | Path, event: dict[str, Any]) -> int:
    with closing(connect(database)) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO events (created_at, source, event_type, severity, message, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event["created_at"],
                event["source"],
                event["event_type"],
                event["severity"],
                event["message"],
                event.get("metadata", "{}"),
            ),
        )
        return int(cursor.lastrowid)


def list_events(database: str | Path, limit: int = 50) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, 200))
    with closing(connect(database)) as connection, connection:
        rows = connection.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (bounded_limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_metrics(database: str | Path) -> dict[str, int]:
    with closing(connect(database)) as connection, connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical,
                SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) AS warning,
                SUM(CASE WHEN severity = 'info' THEN 1 ELSE 0 END) AS info
            FROM events
            """
        ).fetchone()
    return {key: int(row[key] or 0) for key in ("total", "critical", "warning", "info")}
