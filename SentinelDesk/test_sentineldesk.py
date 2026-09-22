import json
import tempfile
import unittest
from pathlib import Path

from backup import backup_database
from detector import analyze_event
from reliability import ReliabilityMetrics
from storage import get_metrics, init_database, list_events, save_event


class SentinelDeskTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.database = Path(handle.name)
        init_database(self.database)

    def tearDown(self):
        self.database.unlink(missing_ok=True)

    def test_detector_classifies_failed_login_as_warning(self):
        event = analyze_event({"message": "Failed login detected"})
        self.assertEqual(event["severity"], "warning")

    def test_detector_classifies_normal_activity_as_info(self):
        event = analyze_event({"message": "Routine inventory completed"})
        self.assertEqual(event["severity"], "info")

    def test_storage_persists_event_and_metrics(self):
        event = analyze_event({"source": "test", "message": "Blocked connection"})
        save_event(self.database, event)
        self.assertEqual(len(list_events(self.database)), 1)
        self.assertEqual(get_metrics(self.database)["warning"], 1)
        self.assertEqual(json.loads(list_events(self.database)[0]["metadata"])["rule"], "Suspicious activity detected")

    def test_detector_rejects_non_object_payload(self):
        with self.assertRaises(ValueError):
            analyze_event(["invalid"])

    def test_runtime_metrics_track_errors_and_latency(self):
        metrics = ReliabilityMetrics()
        metrics.observe_request(200, 12.5)
        metrics.observe_request(500, 30.0)
        snapshot = metrics.snapshot()
        self.assertEqual(snapshot["requests"], 2)
        self.assertEqual(snapshot["errors"], 1)
        self.assertEqual(snapshot["error_rate_percent"], 50.0)

    def test_database_backup_creates_copy(self):
        save_event(self.database, analyze_event({"message": "Backup test"}))
        backup_dir = self.database.parent / f"{self.database.stem}-backups"
        try:
            target = backup_database(self.database, backup_dir)
            self.assertTrue(target.exists())
            self.assertEqual(target.stat().st_size, self.database.stat().st_size)
        finally:
            target.unlink(missing_ok=True)
            backup_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
