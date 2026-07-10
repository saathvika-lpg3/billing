from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict


def _ensure_log_dir() -> Path:
    base = Path(__file__).resolve().parents[1]
    log_dir = base / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def run_startup_db_diagnostics(sqlite_path: Path, use_sqlite: bool) -> Dict[str, object]:
    """Run quick diagnostics for the DB at startup and write a short log.

    Returns a small summary dict. This function is intentionally lightweight
    and tolerant of failures so it can run during app startup.
    """
    log_dir = _ensure_log_dir()
    log_file = log_dir / "db_startup.log"
    logger = logging.getLogger("prm.dbdiag")
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    summary: Dict[str, object] = {
        "use_sqlite": use_sqlite,
        "sqlite_path": str(sqlite_path),
        "sqlite_exists": sqlite_path.exists(),
        "sqlite_size_bytes": None,
        "tables": {},
    }

    try:
        if sqlite_path.exists():
            summary["sqlite_size_bytes"] = sqlite_path.stat().st_size
            with sqlite3.connect(sqlite_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                rows = [r[0] for r in cur.fetchall()]
                for t in rows:
                    try:
                        cur.execute(f"SELECT COUNT(1) FROM {t}")
                        cnt = cur.fetchone()[0]
                    except Exception:
                        cnt = None
                    summary["tables"][t] = cnt
    except Exception as e:
        logger.exception("DB diagnostics failed: %s", e)

    try:
        logger.info("Startup DB diagnostics: %s", summary)
    except Exception:
        pass

    return summary
