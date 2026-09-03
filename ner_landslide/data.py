"""
STEP 2 — Collect (or invent, for practice) sensor readings.

A real system would pull rainfall from IMD, slope from DEM maps,
and past events from GSI. For learning, we *simulate* those sensors
with realistic monsoon patterns for NER.

Why simulate? So you can train a model today, without waiting for
government APIs or satellite accounts.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ner_landslide.config import FEATURE_COLUMNS, GENERATED_DIR, STATIONS


def _monsoon_rain(day_of_year: int, rng: np.random.Generator, multiplier: float) -> float:
    """
    NER monsoon is roughly June–September (days 152–273).
    Rain is low in winter, medium in pre-monsoon storms, very high in monsoon.
    """
    if 152 <= day_of_year <= 273:
        base = rng.gamma(shape=2.2, scale=28)  # often 20–80 mm, sometimes much more
        if rng.random() < 0.12:
            base += rng.uniform(80, 220)  # cloudburst-like day
    elif 90 <= day_of_year <= 151:
        base = rng.gamma(shape=1.4, scale=10)
    else:
        base = rng.gamma(shape=1.1, scale=3)
    return float(max(0.0, base * multiplier))


def _nature_score(row: dict) -> float:
    """
    Hidden "physics-ish" formula that creates labels.

    The AI never sees this function. It only sees the numbers + the yes/no
    landslide column, and has to *learn* the pattern. That is supervised learning.
    """
    rain_24 = row["rainfall_24h_mm"] / 200.0
    rain_72 = row["rainfall_72h_mm"] / 400.0
    slope = row["slope_deg"] / 45.0
    moisture = row["soil_moisture"]
    veg = 1.0 - row["vegetation_cover"]  # less plants → weaker slope
    prior = min(row["prior_events"] / 8.0, 1.0)
    elevation_stress = min(row["elevation_m"] / 2500.0, 1.0) * 0.15

    score = (
        0.28 * min(rain_24, 1.4)
        + 0.32 * min(rain_72, 1.4)
        + 0.22 * slope
        + 0.12 * moisture
        + 0.08 * veg
        + 0.06 * prior
        + elevation_stress
    )
    # Combination rule: steep + soaked is extra dangerous.
    if row["rainfall_72h_mm"] > 160 and row["slope_deg"] > 30:
        score += 0.18
    return float(score)


def generate_history(days: int = 400, seed: int = 42) -> pd.DataFrame:
    """Create one row per station per day."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    for station in STATIONS:
        rain_mult = float(station.get("rain_multiplier", 1.0))
        prior = int(rng.integers(0, 6))
        rain_window = [0.0, 0.0, 0.0]
        moisture = 0.35 + rng.random() * 0.1

        for day in range(days):
            doy = (day % 365) + 1
            rain = _monsoon_rain(doy, rng, rain_mult)
            rain_window = (rain_window + [rain])[-3:]
            rain_72 = float(sum(rain_window))

            # Soil stays wet after rain, dries slowly.
            moisture = 0.82 * moisture + 0.18 * min(rain / 80.0, 1.0)
            moisture = float(np.clip(moisture, 0.08, 0.98))

            slope = float(np.clip(station["base_slope"] + rng.normal(0, 1.2), 5, 55))
            veg = float(np.clip(station["vegetation"] + rng.normal(0, 0.03), 0.2, 0.95))

            row = {
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=day),
                "station_id": station["id"],
                "station_name": station["name"],
                "state": station["state"],
                "lat": station["lat"],
                "lon": station["lon"],
                "rainfall_24h_mm": round(rain, 1),
                "rainfall_72h_mm": round(rain_72, 1),
                "slope_deg": round(slope, 1),
                "soil_moisture": round(moisture, 3),
                "elevation_m": station["base_elevation"],
                "vegetation_cover": round(veg, 3),
                "prior_events": prior,
            }
            score = _nature_score(row)
            noise = rng.normal(0, 0.08)
            row["landslide_occurred"] = int(score + noise > 0.72)
            if row["landslide_occurred"]:
                prior += 1
            rows.append(row)

    return pd.DataFrame(rows)


def save_history(df: pd.DataFrame) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_DIR / "ner_history.csv"
    df.to_csv(path, index=False)
    return path


def load_history() -> pd.DataFrame:
    path = GENERATED_DIR / "ner_history.csv"
    if not path.exists():
        df = generate_history()
        save_history(df)
        return df
    return pd.read_csv(path, parse_dates=["date"])


def latest_snapshot(history: pd.DataFrame | None = None) -> pd.DataFrame:
    """Most recent day for every station — what the live dashboard shows."""
    df = history if history is not None else load_history()
    latest_day = df["date"].max()
    return df[df["date"] == latest_day].copy()


def features_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df[FEATURE_COLUMNS].copy()
