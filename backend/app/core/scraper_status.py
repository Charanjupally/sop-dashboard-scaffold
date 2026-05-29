from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRAPERS_DIR = ROOT_DIR / "scrapers"
STATUS_DB_PATH = SCRAPERS_DIR / "scraper_status.sqlite"


@dataclass
class ScraperLogRow:
    scraper_name: str
    last_run: str | None
    last_status: str | None
    details: str | None


def _ensure_db() -> None:
    STATUS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(STATUS_DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scraper_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_name TEXT NOT NULL,
                last_run TEXT NOT NULL,
                last_status TEXT NOT NULL,
                details TEXT
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scraper_runs_name_run ON scraper_runs(scraper_name, last_run DESC)")


def load_scraper_configs() -> list[dict[str, Any]]:
    configs_dir = SCRAPERS_DIR / "config"
    configs: list[dict[str, Any]] = []
    for file_path in sorted(configs_dir.glob("*.yaml")):
        with file_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        config["file"] = file_path.name
        configs.append(config)
    return configs


def get_latest_scraper_logs() -> dict[str, ScraperLogRow]:
    _ensure_db()
    with sqlite3.connect(STATUS_DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT scraper_name, last_run, last_status, details
            FROM scraper_runs
            WHERE id IN (
                SELECT MAX(id)
                FROM scraper_runs
                GROUP BY scraper_name
            )
            """
        ).fetchall()
    return {
        row["scraper_name"]: ScraperLogRow(
            scraper_name=row["scraper_name"],
            last_run=row["last_run"],
            last_status=row["last_status"],
            details=row["details"],
        )
        for row in rows
    }


def record_scraper_run(scraper_name: str, last_status: str, details: str | None = None) -> None:
    _ensure_db()
    with sqlite3.connect(STATUS_DB_PATH) as connection:
        connection.execute(
            "INSERT INTO scraper_runs (scraper_name, last_run, last_status, details) VALUES (?, ?, ?, ?)",
            (
                scraper_name,
                datetime.now(timezone.utc).isoformat(),
                last_status,
                details,
            ),
        )


def build_scraper_health_rows() -> list[dict[str, Any]]:
    configs = load_scraper_configs()
    logs = get_latest_scraper_logs()
    rows: list[dict[str, Any]] = []

    for config in configs:
        name = config.get("name")
        log = logs.get(name)
        rows.append(
            {
                "name": name,
                "enabled": config.get("enabled") is True,
                "rate_limit_seconds": config.get("rate_limit_seconds"),
                "last_run": log.last_run if log else None,
                "last_status": log.last_status if log else None,
                "sop_trigger": config.get("sop_trigger"),
                "notes": config.get("notes"),
                "fallback": config.get("fallback"),
            }
        )

    return rows
