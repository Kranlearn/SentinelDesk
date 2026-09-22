from __future__ import annotations

import os
from pathlib import Path


VERSION = "0.2.0"
DEFAULT_HOST = os.getenv("SENTINEL_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("SENTINEL_PORT", "8010"))
DEFAULT_DATABASE = Path(os.getenv("SENTINEL_DATABASE", Path(__file__).with_name("sentineldesk.db")))
MAX_REQUEST_BYTES = int(os.getenv("SENTINEL_MAX_REQUEST_BYTES", "16384"))
