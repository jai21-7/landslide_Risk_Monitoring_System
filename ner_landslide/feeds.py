"""
Data adapters (clause a of the problem statement).

Real deployments would call:
  - IMD district rainfall / AWS
  - soil-moisture IoT
  - NRSC / Bhuvan satellite scenes
  - CartoDEM / SRTM slope
  - GSI landslide inventory

Each function has the same shape: input station snapshot → extra fields.
Swap the body later without changing the dashboard.
"""

from __future__ import annotations

from datetime import datetime, timezone


def attach_live_feeds(rows: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for row in rows:
        item = dict(row)
        item["feeds"] = {
            "imd_rainfall": {
                "source": "IMD demo feed (replace with live AWS/district API)",
                "updated": now,
                "rain_24h_mm": row["rainfall_24h_mm"],
                "rain_72h_mm": row["rainfall_72h_mm"],
            },
            "soil_sensor": {
                "source": "IoT soil probe demo",
                "updated": now,
                "moisture": row["soil_moisture"],
                "sensor_id": f"SOIL-{row['station_id']}",
            },
            "satellite": {
                "source": "NRSC/Bhuvan-style NDVI proxy from vegetation_cover",
                "updated": now,
                "ndvi": row["vegetation_cover"],
                "scene": "demo-sentinel-2",
            },
            "terrain": {
                "source": "CartoDEM / SRTM demo",
                "slope_deg": row["slope_deg"],
                "elevation_m": row["elevation_m"],
            },
            "gsi_history": {
                "source": "GSI inventory demo",
                "prior_events": int(row["prior_events"]),
            },
        }
        out.append(item)
    return out
