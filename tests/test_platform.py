from app import app
from ner_landslide.forecast import forecast_rows
from ner_landslide.gis import enrich_assets, heatmap_points
from ner_landslide.notify import render_message
from ner_landslide.priority import prioritise


def test_learn_maps_official_clauses():
    client = app.test_client()
    res = client.get("/learn")
    assert res.status_code == 200
    assert b"SIH26001 mapped" in res.data


def test_ops_and_report_pages():
    client = app.test_client()
    assert client.get("/ops").status_code == 200
    assert client.get("/report").status_code == 200
    assert client.get("/manifest.webmanifest").status_code == 200
    assert client.get("/sw.js").status_code == 200


def test_hindi_alert_text():
    msg = render_message("hi", "Haflong (Dima Hasao)", "Assam", "High", 0.66)
    assert "भूस्खलन" in msg
    assert "Haflong" in msg


def test_heatmap_and_roads_use_station_risk():
    stations = [
        {
            "station_id": "AS-HFL",
            "station_name": "Haflong (Dima Hasao)",
            "level": "Severe",
            "probability": 0.9,
            "color": "#8b1e1e",
            "risk_probability": 0.9,
        }
    ]
    heat = heatmap_points(stations)
    assert heat and heat[0][2] >= 0.8
    assets = enrich_assets(stations, {"AS-HFL"})
    haflong_roads = [r for r in assets["roads"] if r["station_id"] == "AS-HFL"]
    assert haflong_roads
    assert haflong_roads[0]["status"] == "Blocked"


def test_forecast_has_three_horizons():
    row = {
        "station_id": "ML-CHP",
        "station_name": "Cherrapunji escarpment",
        "state": "Meghalaya",
        "lat": 25.3,
        "lon": 91.7,
        "rainfall_24h_mm": 120,
        "rainfall_72h_mm": 260,
        "slope_deg": 40,
        "soil_moisture": 0.8,
        "elevation_m": 1484,
        "vegetation_cover": 0.7,
        "prior_events": 3,
    }
    out = forecast_rows(row)
    assert [x["horizon_h"] for x in out] == [24, 48, 72]


def test_priority_puts_severe_first():
    scored = [
        {"station_id": "TR-AGT", "station_name": "Agartala hills", "state": "Tripura", "level": "Low", "color": "#2f6f4e", "probability": 0.1, "lat": 23.8, "lon": 91.2},
        {"station_id": "AR-TWG", "station_name": "Tawang highway", "state": "Arunachal Pradesh", "level": "Severe", "color": "#8b1e1e", "probability": 0.92, "lat": 27.5, "lon": 91.8},
    ]
    assets = enrich_assets(scored)
    order = prioritise(scored, assets, [])
    assert order[0]["station_id"] == "AR-TWG"


def test_field_report_and_sync(monkeypatch, tmp_path):
    import ner_landslide.store as store

    monkeypatch.setattr(store, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(store, "UPLOAD_DIR", tmp_path / "up")
    client = app.test_client()
    res = client.post(
        "/api/reports",
        json={
            "reporter_role": "citizen",
            "category": "blocked_road",
            "lat": 25.16,
            "lon": 93.01,
            "note": "NH ghat blocked",
        },
    )
    assert res.status_code == 201
    listed = client.get("/api/reports").get_json()
    assert listed and listed[0]["category"] == "blocked_road"
    sync = client.post(
        "/api/sync",
        json={"reports": [{"lat": 27.3, "lon": 88.6, "category": "crack", "note": "wall crack"}]},
    )
    assert sync.status_code == 200
    assert sync.get_json()["synced"] == 1
