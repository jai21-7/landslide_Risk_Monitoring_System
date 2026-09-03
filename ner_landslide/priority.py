"""Emergency response queue: who to help first when many slopes fail at once."""

from __future__ import annotations

from ner_landslide.gis import VILLAGES, ROADS, INFRA


def prioritise(scored: list[dict], assets: dict, reports: list[dict]) -> list[dict]:
    by_id = {s["station_id"]: s for s in scored}
    report_weight = {}
    for rep in reports:
        # nearest station by crude distance
        nearest = min(
            scored,
            key=lambda s: abs(s["lat"] - rep["lat"]) + abs(s["lon"] - rep["lon"]),
            default=None,
        )
        if nearest:
            report_weight[nearest["station_id"]] = report_weight.get(nearest["station_id"], 0) + 1.2

    rows = []
    for station in scored:
        sid = station["station_id"]
        pop = sum(v["population"] for v in VILLAGES if v["station_id"] == sid)
        roads = [r for r in assets["roads"] if r["station_id"] == sid]
        closed = sum(1 for r in roads if r["status"] in {"Closed / isolated", "Blocked"})
        health = sum(1 for i in INFRA if i["station_id"] == sid and i["kind"] == "health")
        p = float(station.get("probability") or 0)
        score = (
            p * 40
            + (pop / 2500)
            + closed * 8
            + health * 3
            + report_weight.get(sid, 0) * 5
        )
        if station["level"] == "Severe":
            action = "Evacuate / keep corridor closed; send SDRF first."
        elif station["level"] == "High":
            action = "Stage earth-movers and ambulances; restrict NH/SH."
        elif station["level"] == "Moderate":
            action = "Patrol drains and cut-slopes; warn bus operators."
        else:
            action = "Routine watch by field staff."
        rows.append(
            {
                "station_id": sid,
                "station_name": station["station_name"],
                "state": station["state"],
                "level": station["level"],
                "color": station["color"],
                "probability": p,
                "people_exposed": pop,
                "roads_affected": closed,
                "field_reports": int(report_weight.get(sid, 0) / 1.2) if sid in report_weight else 0,
                "priority_score": round(score, 1),
                "action": action,
            }
        )
    rows.sort(key=lambda r: r["priority_score"], reverse=True)
    return rows
