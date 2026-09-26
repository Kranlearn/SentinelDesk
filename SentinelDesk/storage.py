from __future__ import annotations

import sqlite3
import hashlib
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import DEFAULT_DATABASE


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
        columns = {row[1] for row in connection.execute("PRAGMA table_info(events)")}
        if "fingerprint" not in columns:
            connection.execute("ALTER TABLE events ADD COLUMN fingerprint TEXT")
        if "occurrences" not in columns:
            connection.execute("ALTER TABLE events ADD COLUMN occurrences INTEGER NOT NULL DEFAULT 1")
        if "first_seen" not in columns:
            connection.execute("ALTER TABLE events ADD COLUMN first_seen TEXT")
        if "last_seen" not in columns:
            connection.execute("ALTER TABLE events ADD COLUMN last_seen TEXT")
        connection.execute("UPDATE events SET first_seen = created_at WHERE first_seen IS NULL")
        connection.execute("UPDATE events SET last_seen = created_at WHERE last_seen IS NULL")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_fingerprint ON events(fingerprint, last_seen)"
        )


def event_fingerprint(event: dict[str, Any]) -> str:
    identity = "\x1f".join(
        str(event.get(key, "")).strip().lower()
        for key in ("source", "event_type", "severity", "message")
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def save_event_details(
    database: str | Path,
    event: dict[str, Any],
    aggregation_window_seconds: int = 60,
) -> dict[str, Any]:
    fingerprint = event_fingerprint(event)
    created_at = event["created_at"]
    cutoff = _parse_timestamp(created_at) - timedelta(seconds=max(0, aggregation_window_seconds))
    with closing(connect(database)) as connection, connection:
        existing = connection.execute(
            """
            SELECT id, occurrences, last_seen FROM events
            WHERE fingerprint = ? AND last_seen >= ?
            ORDER BY last_seen DESC LIMIT 1
            """,
            (fingerprint, cutoff.isoformat(timespec="seconds")),
        ).fetchone()
        if existing:
            occurrences = int(existing["occurrences"] or 1) + 1
            connection.execute(
                "UPDATE events SET occurrences = ?, last_seen = ? WHERE id = ?",
                (occurrences, created_at, existing["id"]),
            )
            return {"id": int(existing["id"]), "aggregated": True, "occurrences": occurrences}

        cursor = connection.execute(
            """
            INSERT INTO events (created_at, source, event_type, severity, message, metadata, fingerprint, occurrences, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                created_at,
                event["source"],
                event["event_type"],
                event["severity"],
                event["message"],
                event.get("metadata", "{}"),
                fingerprint,
                created_at,
                created_at,
            ),
        )
        return {"id": int(cursor.lastrowid), "aggregated": False, "occurrences": 1}


def save_event(database: str | Path, event: dict[str, Any]) -> int:
    return int(save_event_details(database, event)["id"])


def list_events(database: str | Path, limit: int = 50) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, 200))
    with closing(connect(database)) as connection, connection:
        rows = connection.execute("SELECT * FROM events ORDER BY last_seen DESC, id DESC LIMIT ?", (bounded_limit,)).fetchall()
    return [dict(row) for row in rows]


def get_metrics(database: str | Path) -> dict[str, int]:
    with closing(connect(database)) as connection, connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(occurrences), 0) AS occurrences_total,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical,
                SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) AS warning,
                SUM(CASE WHEN severity = 'info' THEN 1 ELSE 0 END) AS info
            FROM events
            """
        ).fetchone()
    return {key: int(row[key] or 0) for key in ("total", "critical", "warning", "info", "occurrences_total")}


def check_database(database: str | Path) -> dict[str, Any]:
    path = Path(database)
    with closing(connect(database)) as connection:
        connection.execute("SELECT 1").fetchone()
    return {"status": "ok", "path": str(path), "size_bytes": path.stat().st_size if path.exists() else 0}
