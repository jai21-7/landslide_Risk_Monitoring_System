"""Weather-linked 72-hour risk forecast (dashboard clause f)."""

from __future__ import annotations

import pandas as pd

from ner_landslide.alerts import attach_alerts
from ner_landslide.model import predict_risk


def forecast_rows(station_row: dict, horizons=(24, 48, 72)) -> list[dict]:
    """
    Simple persistence forecast: tomorrow keeps a fraction of today's rain
    (monsoon does not vanish overnight). Then the same AI model scores it.
    """
    out = []
    rain24 = float(station_row["rainfall_24h_mm"])
    rain72 = float(station_row["rainfall_72h_mm"])
    moisture = float(station_row["soil_moisture"])
    for hours in horizons:
        factor = 0.85 if hours == 24 else (0.7 if hours == 48 else 0.55)
        nxt = dict(station_row)
        nxt["rainfall_24h_mm"] = round(rain24 * factor + (12 if hours == 24 else 6), 1)
        nxt["rainfall_72h_mm"] = round(max(nxt["rainfall_24h_mm"], rain72 * factor), 1)
        nxt["soil_moisture"] = round(min(0.98, moisture * 0.9 + 0.08 * factor), 3)
        nxt["horizon_h"] = hours
        scored = attach_alerts(predict_risk(pd.DataFrame([nxt])))
        rec = scored.iloc[0].to_dict()
        rec["horizon_h"] = hours
        out.append(rec)
    return out


def forecast_all(stations: list[dict]) -> list[dict]:
    pack = []
    for row in stations:
        for item in forecast_rows(row):
            pack.append(
                {
                    "station_id": item["station_id"],
                    "station_name": item["station_name"],
                    "state": item["state"],
                    "horizon_h": item["horizon_h"],
                    "level": item["level"],
                    "probability": item["probability"],
                    "color": item["color"],
                    "rainfall_24h_mm": item["rainfall_24h_mm"],
                }
            )
    return pack
