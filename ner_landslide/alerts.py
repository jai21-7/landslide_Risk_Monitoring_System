"""
STEP 4 — Turn a probability into a human warning.

The model outputs a number between 0 and 1 (chance of a landslide).
People need colours and actions, not decimals.

This file is the "early warning" layer: thresholds, SMS-style messages,
and a simple rule that can raise the level if rain is extreme even when
the model is cautious.
"""

from __future__ import annotations

from ner_landslide.config import ALERT_LEVELS


def alert_from_probability(probability: float) -> dict:
    p = max(0.0, min(float(probability), 1.0))
    for level in ALERT_LEVELS:
        if level["min"] <= p < level["max"]:
            return {
                "level": level["name"],
                "color": level["color"],
                "advice": level["advice"],
                "probability": round(p, 3),
            }
    last = ALERT_LEVELS[-1]
    return {
        "level": last["name"],
        "color": last["color"],
        "advice": last["advice"],
        "probability": round(p, 3),
    }


def maybe_upgrade_for_extreme_rain(alert: dict, rainfall_24h_mm: float, rainfall_72h_mm: float) -> dict:
    """
    Safety net used in real EWSS (early warning systems):
    if rain crosses a danger line, never stay on 'Low'.
    """
    upgraded = dict(alert)
    if rainfall_24h_mm >= 150 or rainfall_72h_mm >= 280:
        if alert["level"] in {"Low", "Moderate"}:
            upgraded.update(
                {
                    "level": "High",
                    "color": "#d35400",
                    "advice": "Rainfall crossed a safety threshold. Treat as High even if the model is unsure.",
                    "rule_override": True,
                }
            )
    if rainfall_24h_mm >= 220 or rainfall_72h_mm >= 400:
        upgraded.update(
            {
                "level": "Severe",
                "color": "#8b1e1e",
                "advice": "Extreme rainfall. Issue immediate public warning.",
                "rule_override": True,
            }
        )
    return upgraded


def format_alert_message(station_name: str, state: str, alert: dict) -> str:
    pct = int(round(alert["probability"] * 100))
    return (
        f"NER LANDSLIDE ALERT — {alert['level'].upper()} | "
        f"{station_name}, {state} | model risk {pct}% | {alert['advice']}"
    )


def attach_alerts(df):
    """Add level, colour, advice, and a ready-to-send message to each row."""
    records = []
    for row in df.to_dict(orient="records"):
        alert = alert_from_probability(row["risk_probability"])
        alert = maybe_upgrade_for_extreme_rain(
            alert, row["rainfall_24h_mm"], row["rainfall_72h_mm"]
        )
        row.update(alert)
        row["message"] = format_alert_message(row["station_name"], row["state"], alert)
        records.append(row)
    import pandas as pd

    return pd.DataFrame(records)
