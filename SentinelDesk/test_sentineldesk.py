import json
import tempfile
import unittest
from pathlib import Path

from detector import analyze_event
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


if __name__ == "__main__":
    unittest.main()
