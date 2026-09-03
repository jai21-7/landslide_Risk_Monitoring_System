"""SQLite store for field reports and dispatched warnings (cloud-shaped, local file)."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ner_landslide.config import DATA_DIR, ROOT

DB_PATH = DATA_DIR / "platform.db"
UPLOAD_DIR = DATA_DIR / "uploads"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            reporter_role TEXT,
            category TEXT,
            lat REAL,
            lon REAL,
            note TEXT,
            media_path TEXT,
            media_kind TEXT,
            client_id TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            station_id TEXT,
            level TEXT,
            channel TEXT,
            audience TEXT,
            lang TEXT,
            body TEXT
        )
        """
    )
    conn.commit()
    return conn


def save_upload(file_storage) -> tuple[str, str]:
    """Save photo/video under data/uploads. Returns (relative_path, kind)."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    original = file_storage.filename or "upload.bin"
    suffix = Path(original).suffix.lower() or ".bin"
    kind = "video" if suffix in {".mp4", ".mov", ".webm", ".3gp"} else "image"
    name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / name
    file_storage.save(dest)
    rel = str(dest.relative_to(ROOT))
    return rel, kind


def add_report(payload: dict) -> dict:
    rec = {
        "id": payload.get("id") or uuid.uuid4().hex,
        "created_at": payload.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "reporter_role": payload.get("reporter_role", "citizen"),
        "category": payload.get("category", "other"),
        "lat": float(payload["lat"]),
        "lon": float(payload["lon"]),
        "note": payload.get("note", ""),
        "media_path": payload.get("media_path"),
        "media_kind": payload.get("media_kind"),
        "client_id": payload.get("client_id"),
    }
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO reports
            (id, created_at, reporter_role, category, lat, lon, note, media_path, media_kind, client_id)
            VALUES (:id, :created_at, :reporter_role, :category, :lat, :lon, :note, :media_path, :media_kind, :client_id)
            """,
            rec,
        )
        conn.commit()
    return rec


def list_reports(limit: int = 100) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def blocked_station_ids(stations: list[dict], radius_deg: float = 0.35) -> set[str]:
    """If a field report says a road is blocked, mark nearby monitoring sites."""
    blocked: set[str] = set()
    reports = [r for r in list_reports() if r["category"] == "blocked_road"]
    for report in reports:
        for st in stations:
            dlat = abs(st["lat"] - report["lat"])
            dlon = abs(st["lon"] - report["lon"])
            if dlat + dlon < radius_deg:
                blocked.add(st["station_id"])
    return blocked


def add_notification(payload: dict) -> dict:
    rec = {
        "id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO notifications
            (id, created_at, station_id, level, channel, audience, lang, body)
            VALUES (:id, :created_at, :station_id, :level, :channel, :audience, :lang, :body)
            """,
            rec,
        )
        conn.commit()
    return rec


def list_notifications(limit: int = 80) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def already_sent_today(station_id: str, level: str, audience: str, lang: str) -> bool:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM notifications
            WHERE station_id = ? AND level = ? AND audience = ? AND lang = ?
              AND substr(created_at, 1, 10) = ?
            LIMIT 1
            """,
            (station_id, level, audience, lang, day),
        ).fetchone()
    return row is not None
