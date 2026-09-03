"""Checks a beginner can run: pytest -q"""

from ner_landslide.alerts import alert_from_probability, maybe_upgrade_for_extreme_rain
from ner_landslide.config import STATIONS
from ner_landslide.data import generate_history
from ner_landslide.model import predict_risk, train_model


def test_eight_ner_states_are_covered():
    states = {s["state"] for s in STATIONS}
    assert len(states) == 8


def test_alert_bands():
    assert alert_from_probability(0.1)["level"] == "Low"
    assert alert_from_probability(0.4)["level"] == "Moderate"
    assert alert_from_probability(0.6)["level"] == "High"
    assert alert_from_probability(0.9)["level"] == "Severe"


def test_rain_safety_net_upgrades_low_to_high():
    low = alert_from_probability(0.1)
    up = maybe_upgrade_for_extreme_rain(low, 160, 50)
    assert up["level"] == "High"
    assert up.get("rule_override") is True


def test_model_trains_and_predicts(tmp_path, monkeypatch):
    from ner_landslide import model as model_mod

    monkeypatch.setattr(model_mod, "MODEL_PATH", tmp_path / "m.pkl")
    monkeypatch.setattr(model_mod, "MODEL_DIR", tmp_path)
    df = generate_history(days=400, seed=1)
    metrics = train_model(df, seed=1)
    assert metrics["roc_auc"] > 0.7
    scored = predict_risk(df.tail(12))
    assert "risk_probability" in scored.columns
    assert scored["risk_probability"].between(0, 1).all()
