# NER Landslide Watch — SIH26001

AI-powered early warning and monitoring platform for landslide-prone areas in India’s North Eastern Region (MDoNER · Disaster Management).

This repo is a **working software demo**. IMD weather, NRSC satellite, and SMS gateways are plugged in as **adapters with simulated live data**, so you can run everything without government API keys. Swap the adapter bodies later.

## Problem clauses → code

| Official need | Where it lives |
| --- | --- |
| Rainfall, soil moisture, satellite, terrain, history | `ner_landslide/feeds.py`, `data.py` |
| AI/ML high-risk prediction | `ner_landslide/model.py` |
| Alerts to district / SDMA / community | `ner_landslide/notify.py`, Operations page |
| GIS roads, villages, infrastructure + heatmap | `ner_landslide/gis.py`, `/` |
| Geo-tagged photo/video field reports | `/report`, `ner_landslide/store.py` |
| Severity, road status, weather forecast, response order | `/ops`, `forecast.py`, `priority.py` |
| Multilingual notifications | English, Hindi, Assamese, Bangla |
| Low-network / offline | PWA `sw.js` + queued reports in `report.js` |

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`

- `/` GIS command map  
- `/ops` dashboards + dispatch alerts  
- `/report` citizen / official uploads  
- `/learn` beginner map of the problem statement  

Numbered training scripts still work: `scripts/01_make_data.py`, `02_train_model.py`, `03_print_alerts.py`.

```bash
pytest -q
```

## Honest limits

Simulated feeds and logged “SMS”, not live IMD CAP or a production cloud. Next step is wiring real AWS rainfall, Bhuvan scenes, and an SMS provider into the same adapter functions.
