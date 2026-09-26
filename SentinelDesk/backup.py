from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def backup_database(database: str | Path, destination: str | Path | None = None) -> Path:
    source = Path(database)
    if not source.exists():
        raise FileNotFoundError(source)
    target_dir = Path(destination) if destination else source.parent / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source.stem}-{datetime.now():%Y%m%d-%H%M%S}{source.suffix}"
    shutil.copy2(source, target)
    return target
