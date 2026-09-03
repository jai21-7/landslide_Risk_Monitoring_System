# NER Landslide Watch (SIH26001)

Beginner project: an **AI early-warning and landslide risk map** for India’s North Eastern Region (NER).

Problem statement: *AI-Based early warning and landslide Risk Monitoring System in NER*  
Organization: Ministry of Development of North Eastern Region (MDoNER)  
Domain: Disaster Management · Category: Software · Code: **SIH26001**

This is a teaching prototype. It uses **simulated** rainfall and slope readings so you can learn the full pipeline without government APIs. Swap in real IMD / GSI data later.

## What you will learn

1. How a disaster-monitoring **dataset** is structured  
2. How a small **machine-learning** model predicts risk  
3. How a probability becomes a **colour-coded warning**  
4. How a **Flask** website shows the result on a map  

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the steps (in order)

```bash
python scripts/01_make_data.py      # create sample NER history
python scripts/02_train_model.py    # train Random Forest
python scripts/03_print_alerts.py   # see warnings in the terminal
python app.py                       # open http://127.0.0.1:5000
```

`python app.py` also generates data and trains the model if they are missing, then starts the dashboard.

Pages:

- `/` live map + what-if sliders  
- `/how-it-works` accuracy and which sensors the model trusted  
- `/learn` the same five steps in plain language  

## Project map

```
ner_landslide/config.py   # stations, alert colours
ner_landslide/data.py     # simulate sensors
ner_landslide/model.py    # train + predict
ner_landslide/alerts.py   # Low / Moderate / High / Severe
app.py                    # website
templates/                # HTML
static/style.css
scripts/                  # numbered beginner commands
tests/                    # pytest -q
```

## Tests

```bash
pytest -q
```

## Honest limits

- Rain and landslide labels are **generated**, not official measurements.  
- The map is a **demo**, not an NDMA / MDoNER operational system.  
- Next upgrade: real rain gauges, DEM slope, and historical GSI events.
