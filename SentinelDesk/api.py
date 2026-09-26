from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backup import backup_database
from config import AGGREGATION_WINDOW_SECONDS, DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, MAX_REQUEST_BYTES, VERSION
from detector import analyze_event, demo_events
from logging_config import configure_logging
from reliability import ReliabilityMetrics, RequestTimer
from storage import check_database, get_metrics, init_database, list_events, save_event_details


ROOT = Path(__file__).parent
LOGGER = configure_logging()
RUNTIME_METRICS = ReliabilityMetrics()


class ApiHandler(BaseHTTPRequestHandler):
    database = DEFAULT_DATABASE

    def _request_timer(self) -> RequestTimer:
        return RequestTimer(RUNTIME_METRICS, LOGGER, self.command, urlparse(self.path).path)

    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename: str, content_type: str) -> None:
        path = ROOT / filename
        if not path.exists():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        timer = self._request_timer()
        status = 200
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_file("dashboard.html", "text/html; charset=utf-8")
            elif parsed.path == "/dashboard.css":
                self._send_file("dashboard.css", "text/css; charset=utf-8")
            elif parsed.path == "/dashboard.js":
                self._send_file("dashboard.js", "application/javascript; charset=utf-8")
            elif parsed.path == "/api/health":
                self._send_json({"status": "ok", "service": "SentinelDesk", "version": VERSION})
            elif parsed.path == "/api/ready":
                self._send_json({"status": "ready", "database": check_database(self.database)})
            elif parsed.path == "/api/version":
                self._send_json({"service": "SentinelDesk", "version": VERSION})
            elif parsed.path == "/api/metrics":
                self._send_json({"events": get_metrics(self.database), "runtime": RUNTIME_METRICS.snapshot()})
            elif parsed.path == "/api/events":
                query = parse_qs(parsed.query)
                try:
                    limit = int(query.get("limit", [50])[0])
                except ValueError:
                    self._send_json({"error": "limit must be an integer"}, 400)
                    return
                self._send_json({"events": list_events(self.database, limit)})
            else:
                status = 404
                self._send_json({"error": "Not found"}, status)
        except Exception:
            status = 500
            LOGGER.exception("request_failed", extra={"event": "request_failed"})
            self._send_json({"error": "Internal server error"}, status)
        finally:
            timer.finish(status)

    def do_POST(self) -> None:
        timer = self._request_timer()
        status = 201
        try:
            if self.path not in ("/api/events", "/api/demo"):
                if self.path == "/api/backup":
                    target = backup_database(self.database)
                    self._send_json({"status": "created", "path": str(target)}, 201)
                    return
                status = 404
                self._send_json({"error": "Not found"}, status)
                return

            if self.path == "/api/demo":
                events = demo_events()
            else:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    status = 413
                    self._send_json({"error": f"Request body must be between 1 and {MAX_REQUEST_BYTES} bytes"}, status)
                    return
                try:
                    payload = json.loads(self.rfile.read(length))
                    events = [payload]
                except (UnicodeDecodeError, json.JSONDecodeError):
                    status = 400
                    self._send_json({"error": "Invalid JSON body"}, status)
                    return

            created = []
            for raw_event in events:
                event = analyze_event(raw_event)
                result = save_event_details(self.database, event, AGGREGATION_WINDOW_SECONDS)
                created.append({**result, **event})
            self._send_json({"created": created}, status)
        except ValueError as error:
            status = 400
            self._send_json({"error": str(error)}, status)
        except Exception:
            status = 500
            LOGGER.exception("request_failed", extra={"event": "request_failed"})
            self._send_json({"error": "Internal server error"}, status)
        finally:
            timer.finish(status)

    def log_message(self, format: str, *args: object) -> None:
        return


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, database: str | Path = DEFAULT_DATABASE) -> None:
    init_database(database)
    ApiHandler.database = database
    server = ThreadingHTTPServer((host, port), ApiHandler)
    LOGGER.info("server_started", extra={"event": "server_started", "path": f"http://{host}:{port}"})
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArret de SentinelDesk")
    finally:
        server.server_close()


if __name__ == "__main__":
    run(
        host=os.getenv("SENTINEL_HOST", DEFAULT_HOST),
        port=int(os.getenv("SENTINEL_PORT", str(DEFAULT_PORT))),
        database=os.getenv("SENTINEL_DATABASE", str(DEFAULT_DATABASE)),
    )
