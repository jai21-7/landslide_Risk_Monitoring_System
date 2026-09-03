"""
SIH26001 web platform: GIS command view, field reports, alerts, forecasts.

Run:  python app.py
Open: http://127.0.0.1:5000
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

from ner_landslide.alerts import attach_alerts
from ner_landslide.config import DATA_DIR, FEATURE_COLUMNS, STATIONS, station_by_id
from ner_landslide.data import generate_history, latest_snapshot, load_history, save_history
from ner_landslide.feeds import attach_live_feeds
from ner_landslide.forecast import forecast_all
from ner_landslide.gis import enrich_assets, heatmap_points
from ner_landslide.model import load_bundle, predict_risk, train_model
from ner_landslide.notify import LANGS, dispatch_for_station, render_message
from ner_landslide.priority import prioritise
from ner_landslide.store import (
    UPLOAD_DIR,
    add_report,
    blocked_station_ids,
    list_notifications,
    list_reports,
    save_upload,
)

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024


def _ensure_ready() -> None:
    load_history()
    load_bundle()


def _json_records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    if "date" in out.columns:
        out["date"] = out["date"].astype(str)
    return out.to_dict(orient="records")


def _live_table() -> pd.DataFrame:
    return attach_alerts(predict_risk(latest_snapshot()))


def _platform(lang: str = "en") -> dict:
    _ensure_ready()
    stations = attach_live_feeds(_json_records(_live_table()))
    reports = list_reports()
    blocked = blocked_station_ids(stations)
    assets = enrich_assets(stations, blocked)
    return {
        "stations": stations,
        "heatmap": heatmap_points(stations),
        "assets": assets,
        "reports": reports,
        "forecast": forecast_all(stations),
        "priority": prioritise(stations, assets, reports),
        "notifications": list_notifications(),
        "langs": LANGS,
        "lang": lang if lang in LANGS else "en",
        "counts": {
            "severe": sum(1 for s in stations if s["level"] == "Severe"),
            "high": sum(1 for s in stations if s["level"] == "High"),
            "blocked_roads": sum(1 for r in assets["roads"] if r["status"] in {"Closed / isolated", "Blocked"}),
            "reports": len(reports),
        },
    }


@app.route("/")
def dashboard():
    state = _platform()
    worst = max(state["stations"], key=lambda s: s.get("probability") or 0)
    return render_template("dashboard.html", state=state, worst=worst)


@app.route("/ops")
def ops():
    return render_template("ops.html", state=_platform(request.args.get("lang", "en")))


@app.route("/report")
def report_page():
    return render_template("report.html")


@app.route("/learn")
def learn():
    return render_template("learn.html")


@app.route("/how-it-works")
def how_it_works():
    _ensure_ready()
    bundle = load_bundle()
    importance = sorted(
        bundle["metrics"]["feature_importance"].items(),
        key=lambda item: item[1],
        reverse=True,
    )
    return render_template(
        "how_it_works.html",
        metrics=bundle["metrics"],
        importance=importance,
        features=FEATURE_COLUMNS,
    )


@app.route("/offline")
def offline():
    return render_template("offline.html")


@app.route("/api/platform")
def api_platform():
    return jsonify(_platform(request.args.get("lang", "en")))


@app.route("/api/stations")
def api_stations():
    return jsonify(_platform()["stations"])


@app.route("/api/history/<station_id>")
def api_history(station_id: str):
    _ensure_ready()
    df = load_history()
    subset = df[df["station_id"] == station_id].sort_values("date").tail(60)
    if subset.empty:
        return jsonify({"error": "unknown station"}), 404
    return jsonify(_json_records(attach_alerts(predict_risk(subset))))


@app.route("/api/what-if", methods=["POST"])
def api_what_if():
    _ensure_ready()
    body = request.get_json(force=True)
    station_by_id(body["station_id"])
    latest = latest_snapshot()
    row = latest[latest["station_id"] == body["station_id"]].iloc[0].to_dict()
    for key in FEATURE_COLUMNS:
        if key in body:
            row[key] = float(body[key])
    return jsonify(_json_records(attach_alerts(predict_risk(pd.DataFrame([row]))))[0])


@app.route("/api/forecast")
def api_forecast():
    return jsonify(_platform()["forecast"])


@app.route("/api/reports", methods=["GET", "POST"])
def api_reports():
    if request.method == "GET":
        return jsonify(list_reports())
    payload = {
        "id": request.form.get("id") or (request.json.get("id") if request.is_json else None),
        "reporter_role": request.form.get("reporter_role")
        or (request.json.get("reporter_role") if request.is_json else "citizen"),
        "category": request.form.get("category")
        or (request.json.get("category") if request.is_json else "other"),
        "lat": request.form.get("lat") or (request.json.get("lat") if request.is_json else None),
        "lon": request.form.get("lon") or (request.json.get("lon") if request.is_json else None),
        "note": request.form.get("note") or (request.json.get("note") if request.is_json else ""),
        "client_id": request.form.get("client_id")
        or (request.json.get("client_id") if request.is_json else None),
    }
    if request.files.get("media"):
        rel, kind = save_upload(request.files["media"])
        payload["media_path"] = rel
        payload["media_kind"] = kind
    elif request.is_json:
        body = request.get_json(silent=True) or {}
        payload["media_path"] = body.get("media_path")
        payload["media_kind"] = body.get("media_kind")
    rec = add_report(payload)
    return jsonify(rec), 201


@app.route("/api/sync", methods=["POST"])
def api_sync():
    """Offline queue from the field app: list of reports without files, or after files upload."""
    body = request.get_json(force=True)
    items = body if isinstance(body, list) else body.get("reports", [])
    saved = [add_report(item) for item in items]
    return jsonify({"synced": len(saved), "reports": saved})


@app.route("/api/dispatch", methods=["POST"])
def api_dispatch():
    lang = (request.get_json(silent=True) or {}).get("lang") or request.args.get("lang", "en")
    state = _platform(lang)
    sent = []
    for station in state["stations"]:
        sent.extend(dispatch_for_station(station, lang))
    return jsonify({"sent": len(sent), "notifications": sent, "preview": [
        render_message(lang, s["station_name"], s["state"], s["level"], s.get("probability") or 0)
        for s in state["stations"] if s["level"] in {"High", "Severe"}
    ]})


@app.route("/api/notifications")
def api_notifications():
    return jsonify(list_notifications())


@app.route("/api/model")
def api_model():
    _ensure_ready()
    return jsonify(load_bundle()["metrics"])


@app.route("/health")
def health():
    return jsonify({"ok": True, "stations": len(STATIONS), "data_dir": str(DATA_DIR)})


@app.route("/uploads/<path:name>")
def uploads(name: str):
    return send_from_directory(UPLOAD_DIR, name)


@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest")


@app.route("/sw.js")
def service_worker():
    resp = send_from_directory(app.static_folder, "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Content-Type"] = "application/javascript"
    return resp


def bootstrap_cli() -> None:
    print("Generating sample NER history...")
    df = generate_history()
    path = save_history(df)
    print(f"Saved {len(df)} rows → {path}")
    print("Training Random Forest...")
    metrics = train_model(df)
    print(f"Accuracy: {metrics['accuracy']:.3f}  ROC-AUC: {metrics['roc_auc']:.3f}")


if __name__ == "__main__":
    bootstrap_cli()
    print("\nGIS dashboard: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
