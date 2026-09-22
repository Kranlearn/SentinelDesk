from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from detector import analyze_event, demo_events
from storage import DEFAULT_DATABASE, get_metrics, init_database, list_events, save_event


ROOT = Path(__file__).parent


class ApiHandler(BaseHTTPRequestHandler):
    database = DEFAULT_DATABASE

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
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_file("dashboard.html", "text/html; charset=utf-8")
        elif parsed.path == "/dashboard.css":
            self._send_file("dashboard.css", "text/css; charset=utf-8")
        elif parsed.path == "/dashboard.js":
            self._send_file("dashboard.js", "application/javascript; charset=utf-8")
        elif parsed.path == "/api/health":
            self._send_json({"status": "ok", "service": "SentinelDesk"})
        elif parsed.path == "/api/metrics":
            self._send_json(get_metrics(self.database))
        elif parsed.path == "/api/events":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", [50])[0])
            self._send_json({"events": list_events(self.database, limit)})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path not in ("/api/events", "/api/demo"):
            self.send_error(404)
            return

        if self.path == "/api/demo":
            events = demo_events()
        else:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                events = [payload]
            except (ValueError, json.JSONDecodeError):
                self._send_json({"error": "Invalid JSON body"}, 400)
                return

        created = []
        for raw_event in events:
            event = analyze_event(raw_event)
            event_id = save_event(self.database, event)
            created.append({"id": event_id, **event})
        self._send_json({"created": created}, 201)

    def log_message(self, format: str, *args: object) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8010, database: str | Path = DEFAULT_DATABASE) -> None:
    init_database(database)
    ApiHandler.database = database
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"SentinelDesk disponible sur http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArret de SentinelDesk")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
