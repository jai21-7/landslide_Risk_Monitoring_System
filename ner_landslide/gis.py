"""
GIS layers for the command dashboard: villages, hill roads, and
critical infrastructure. A production system would load these from
state GIS cells / PMGSY / NHIDCL. Here they sit next to our stations
so the map can show who gets cut off if a slope fails.
"""

from __future__ import annotations

from ner_landslide.config import STATIONS

# Population is order-of-magnitude (census-style), not a live count.
VILLAGES = [
    {"id": "V-TWG", "name": "Lumla cluster", "state": "Arunachal Pradesh", "lat": 27.55, "lon": 91.72, "population": 4200, "station_id": "AR-TWG"},
    {"id": "V-ITN", "name": "Naharlagun outskirts", "state": "Arunachal Pradesh", "lat": 27.10, "lon": 93.70, "population": 8900, "station_id": "AR-ITN"},
    {"id": "V-HFL", "name": "Haflong basti", "state": "Assam", "lat": 25.18, "lon": 93.02, "population": 6100, "station_id": "AS-HFL"},
    {"id": "V-GHY", "name": "Kharguli hill", "state": "Assam", "lat": 26.19, "lon": 91.76, "population": 12000, "station_id": "AS-GHY"},
    {"id": "V-UKH", "name": "Ukhrul town", "state": "Manipur", "lat": 25.11, "lon": 94.37, "population": 9200, "station_id": "MN-UKH"},
    {"id": "V-CHP", "name": "Sohra villages", "state": "Meghalaya", "lat": 25.27, "lon": 91.73, "population": 5400, "station_id": "ML-CHP"},
    {"id": "V-SHL", "name": "Laitumkhrah rim", "state": "Meghalaya", "lat": 25.57, "lon": 91.90, "population": 15000, "station_id": "ML-SHL"},
    {"id": "V-AIZ", "name": "Durtlang", "state": "Mizoram", "lat": 23.79, "lon": 92.73, "population": 7800, "station_id": "MZ-AIZ"},
    {"id": "V-KOH", "name": "Kohima village", "state": "Nagaland", "lat": 25.69, "lon": 94.11, "population": 11000, "station_id": "NL-KOH"},
    {"id": "V-GTK", "name": "Chandmari", "state": "Sikkim", "lat": 27.35, "lon": 88.62, "population": 6700, "station_id": "SK-GTK"},
    {"id": "V-AGT", "name": "Kunjaban hills", "state": "Tripura", "lat": 23.86, "lon": 91.29, "population": 4300, "station_id": "TR-AGT"},
    {"id": "V-IMP", "name": "Langol foothill", "state": "Manipur", "lat": 24.85, "lon": 93.91, "population": 9800, "station_id": "MN-IMP"},
]

ROADS = [
    {
        "id": "NH-13-TWG",
        "name": "Tawang highway stretch",
        "kind": "NH",
        "station_id": "AR-TWG",
        "coords": [[27.50, 91.80], [27.586, 91.859], [27.64, 91.90]],
    },
    {
        "id": "NH-27-HFL",
        "name": "Haflong–Lumding ghat",
        "kind": "NH",
        "station_id": "AS-HFL",
        "coords": [[25.10, 92.95], [25.164, 93.015], [25.22, 93.08]],
    },
    {
        "id": "NH-6-CHP",
        "name": "Shillong–Sohra road",
        "kind": "SH",
        "station_id": "ML-CHP",
        "coords": [[25.50, 91.82], [25.40, 91.76], [25.30, 91.70]],
    },
    {
        "id": "NH-10-GTK",
        "name": "Gangtok corridor",
        "kind": "NH",
        "station_id": "SK-GTK",
        "coords": [[27.28, 88.55], [27.339, 88.607], [27.39, 88.64]],
    },
    {
        "id": "NH-2-KOH",
        "name": "Kohima ridge road",
        "kind": "NH",
        "station_id": "NL-KOH",
        "coords": [[25.62, 94.08], [25.675, 94.109], [25.73, 94.13]],
    },
    {
        "id": "SH-AIZ",
        "name": "Aizawl hill road",
        "kind": "SH",
        "station_id": "MZ-AIZ",
        "coords": [[23.70, 92.70], [23.727, 92.718], [23.76, 92.73]],
    },
    {
        "id": "SH-UKH",
        "name": "Imphal–Ukhrul road",
        "kind": "SH",
        "station_id": "MN-UKH",
        "coords": [[24.90, 94.10], [25.05, 94.36], [25.11, 94.37]],
    },
    {
        "id": "NH-8-AGT",
        "name": "Agartala approach",
        "kind": "NH",
        "station_id": "TR-AGT",
        "coords": [[23.80, 91.26], [23.832, 91.287], [23.86, 91.30]],
    },
]

INFRA = [
    {"id": "I-PHC-HFL", "name": "Haflong PHC", "kind": "health", "lat": 25.17, "lon": 93.02, "station_id": "AS-HFL"},
    {"id": "I-SCH-CHP", "name": "Sohra school", "kind": "school", "lat": 25.29, "lon": 91.71, "station_id": "ML-CHP"},
    {"id": "I-BRG-GTK", "name": "Ranipool bridge", "kind": "bridge", "lat": 27.29, "lon": 88.59, "station_id": "SK-GTK"},
    {"id": "I-PHC-TWG", "name": "Tawang health post", "kind": "health", "lat": 27.58, "lon": 91.87, "station_id": "AR-TWG"},
    {"id": "I-DEP-AIZ", "name": "Aizawl fire station", "kind": "response", "lat": 23.73, "lon": 92.72, "station_id": "MZ-AIZ"},
    {"id": "I-BRG-KOH", "name": "Kohima junction bridge", "kind": "bridge", "lat": 25.66, "lon": 94.10, "station_id": "NL-KOH"},
]


def heatmap_points(scored_stations: list[dict]) -> list[list[float]]:
    """Leaflet.heat wants [lat, lon, intensity 0-1] around each sensor."""
    points: list[list[float]] = []
    offsets = [
        (0, 0),
        (0.08, 0.05),
        (-0.07, 0.06),
        (0.06, -0.08),
        (-0.05, -0.05),
        (0.12, 0.02),
        (-0.1, 0.04),
    ]
    by_id = {row["station_id"]: row for row in scored_stations}
    for station in STATIONS:
        row = by_id.get(station["id"])
        if not row:
            continue
        intensity = float(row.get("risk_probability") or row.get("probability") or 0)
        for i, (dlat, dlon) in enumerate(offsets):
            fade = 1.0 if i == 0 else 0.55
            points.append([station["lat"] + dlat, station["lon"] + dlon, min(1.0, intensity * fade)])
    return points


def _status_from_level(level: str) -> str:
    if level == "Severe":
        return "Closed / isolated"
    if level == "High":
        return "Restricted"
    if level == "Moderate":
        return "Caution"
    return "Open"


def enrich_assets(scored_stations: list[dict], blocked_station_ids: set[str] | None = None) -> dict:
    blocked = blocked_station_ids or set()
    by_id = {row["station_id"]: row for row in scored_stations}

    def attach(item: dict, extra: dict | None = None) -> dict:
        row = by_id.get(item["station_id"], {})
        level = row.get("level", "Low")
        status = "Blocked" if item["station_id"] in blocked else _status_from_level(level)
        out = {
            **item,
            "risk_level": level,
            "risk_probability": row.get("probability", row.get("risk_probability", 0)),
            "color": row.get("color", "#2f6f4e"),
            "status": status,
            "station_name": row.get("station_name", item["station_id"]),
        }
        if extra:
            out.update(extra)
        return out

    roads = [attach(r) for r in ROADS]
    villages = [attach(v) for v in VILLAGES]
    infra = [attach(i) for i in INFRA]
    return {"roads": roads, "villages": villages, "infrastructure": infra}
