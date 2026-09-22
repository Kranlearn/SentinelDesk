from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


RULES = (
    ("critical", re.compile(r"\b(ransomware|malware|credential theft)\b", re.I), "Threat keyword detected"),
    ("warning", re.compile(r"\b(failed login|unauthorized|blocked|denied)\b", re.I), "Suspicious activity detected"),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def analyze_event(raw: dict[str, Any]) -> dict[str, Any]:
    message = str(raw.get("message", "")).strip()
    source = str(raw.get("source", "local-demo")).strip() or "local-demo"
    event_type = str(raw.get("event_type", "activity")).strip() or "activity"
    severity = "info"
    reason = "Normal activity"

    for candidate, pattern, rule_reason in RULES:
        if pattern.search(message):
            severity = candidate
            reason = rule_reason
            break

    metadata = raw.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {"value": str(metadata)}

    return {
        "created_at": str(raw.get("created_at") or now_iso()),
        "source": source[:80],
        "event_type": event_type[:80],
        "severity": severity,
        "message": message[:500] or "Empty event message",
        "metadata": json.dumps({**metadata, "rule": reason}, ensure_ascii=True),
    }


def demo_events() -> list[dict[str, Any]]:
    return [
        {"source": "Windows Lab", "event_type": "login", "message": "Successful local login"},
        {"source": "Windows Lab", "event_type": "login", "message": "Failed login detected for user demo"},
        {"source": "Local Sensor", "event_type": "network", "message": "Blocked connection on port 445"},
        {"source": "Local Sensor", "event_type": "process", "message": "Routine process inventory completed"},
    ]
