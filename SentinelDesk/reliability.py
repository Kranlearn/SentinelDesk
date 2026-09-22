from __future__ import annotations

import logging
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any


class ReliabilityMetrics:
    def __init__(self) -> None:
        self.started_at = datetime.now(timezone.utc)
        self._lock = threading.Lock()
        self._requests = 0
        self._errors = 0
        self._durations_ms: list[float] = []
        self._status_codes: Counter[str] = Counter()

    def observe_request(self, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._requests += 1
            self._status_codes[str(status_code)] += 1
            self._durations_ms.append(duration_ms)
            if status_code >= 500:
                self._errors += 1
            if len(self._durations_ms) > 500:
                self._durations_ms.pop(0)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            durations = list(self._durations_ms)
            average = sum(durations) / len(durations) if durations else 0.0
            uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()
            return {
                "requests": self._requests,
                "errors": self._errors,
                "error_rate_percent": round((self._errors / self._requests) * 100, 2) if self._requests else 0.0,
                "average_response_ms": round(average, 2),
                "uptime_seconds": round(uptime, 2),
                "status_codes": dict(self._status_codes),
            }


class RequestTimer:
    def __init__(self, metrics: ReliabilityMetrics, logger: logging.Logger, method: str, path: str) -> None:
        self.metrics = metrics
        self.logger = logger
        self.method = method
        self.path = path
        self.started = time.perf_counter()

    def finish(self, status_code: int) -> None:
        duration_ms = (time.perf_counter() - self.started) * 1000
        self.metrics.observe_request(status_code, duration_ms)
        self.logger.info(
            "api_request",
            extra={"event": "api_request", "method": self.method, "path": self.path, "status": status_code, "duration_ms": round(duration_ms, 2)},
        )
