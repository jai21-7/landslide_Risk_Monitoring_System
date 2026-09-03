"""
STEP 5 — Put it on a website so people can see warnings.

Flask is a tiny Python web framework: a function returns a web page.
This file also exposes JSON APIs the map uses.

Run:  python app.py
Then open the URL printed in the terminal.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

from ner_landslide.alerts import attach_alerts
from ner_landslide.config import FEATURE_COLUMNS, STATIONS, station_by_id
from ner_landslide.data import generate_history, latest_snapshot, load_history, save_history
from ner_landslide.model import load_bundle, predict_risk, train_model

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))


def _ensure_ready() -> None:
    """First visit: create sample data and train the model if missing."""
    load_history()
    load_bundle()


def _json_records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    if "date" in out.columns:
        out["date"] = out["date"].astype(str)
    return out.to_dict(orient="records")


def _live_table() -> pd.DataFrame:
    snap = latest_snapshot()
    return attach_alerts(predict_risk(snap))


@app.route("/")
def dashboard():
    _ensure_ready()
    table = _live_table()
    stations = table.to_dict(orient="records")
    counts = table["level"].value_counts().to_dict()
    worst = table.sort_values("risk_probability", ascending=False).iloc[0]
    return render_template(
        "dashboard.html",
        stations=stations,
        counts=counts,
        worst=worst.to_dict(),
        feature_names=FEATURE_COLUMNS,
    )


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


@app.route("/api/stations")
def api_stations():
    _ensure_ready()
    table = _live_table()
    return jsonify(_json_records(table))


@app.route("/api/history/<station_id>")
def api_history(station_id: str):
    _ensure_ready()
    df = load_history()
    subset = df[df["station_id"] == station_id].sort_values("date").tail(60)
    if subset.empty:
        return jsonify({"error": "unknown station"}), 404
    scored = attach_alerts(predict_risk(subset))
    return jsonify(_json_records(scored))


@app.route("/api/what-if", methods=["POST"])
def api_what_if():
    """
    Beginner playground: change rainfall / slope on one station and
    see how the warning colour changes. This is how you *feel* the model.
    """
    _ensure_ready()
    body = request.get_json(force=True)
    station = station_by_id(body["station_id"])
    latest = latest_snapshot()
    row = latest[latest["station_id"] == station["id"]].iloc[0].to_dict()
    for key in FEATURE_COLUMNS:
        if key in body:
            row[key] = float(body[key])
    scored = attach_alerts(predict_risk(pd.DataFrame([row])))
    payload = _json_records(scored)[0]
    return jsonify(payload)


@app.route("/api/model")
def api_model():
    _ensure_ready()
    return jsonify(load_bundle()["metrics"])


@app.route("/health")
def health():
    return jsonify({"ok": True, "stations": len(STATIONS)})


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
    print("\nDashboard: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
