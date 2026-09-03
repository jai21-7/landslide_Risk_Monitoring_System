"""Step 4: score today's snapshot and print human-readable warnings."""

from ner_landslide.alerts import attach_alerts
from ner_landslide.data import latest_snapshot
from ner_landslide.model import predict_risk

if __name__ == "__main__":
    table = attach_alerts(predict_risk(latest_snapshot()))
    cols = ["station_name", "state", "rainfall_24h_mm", "level", "probability"]
    print(table[cols].sort_values("probability", ascending=False).to_string(index=False))
    print("\nExample SMS:\n", table.iloc[0]["message"])
