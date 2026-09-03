"""
STEP 1 — Know the place you are protecting.

The North Eastern Region (NER) of India has eight states.
Landslides are common here because of steep hills + heavy monsoon rain.

This file is a simple "settings sheet": station locations, feature names,
and alert colours. Beginners: change a number here, re-run the app, and
watch the dashboard change.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
GENERATED_DIR = DATA_DIR / "generated"
MODEL_DIR = ROOT / "models"
MODEL_PATH = MODEL_DIR / "landslide_model.pkl"

# Eight NER states + a few extra landslide-prone road/hill sites.
# Coordinates are approximate city / corridor locations (good enough for a demo map).
STATIONS = [
    {
        "id": "AR-ITN",
        "name": "Itanagar hills",
        "state": "Arunachal Pradesh",
        "lat": 27.0844,
        "lon": 93.6053,
        "base_slope": 32,
        "base_elevation": 320,
        "vegetation": 0.62,
    },
    {
        "id": "AR-TWG",
        "name": "Tawang highway",
        "state": "Arunachal Pradesh",
        "lat": 27.5860,
        "lon": 91.8590,
        "base_slope": 41,
        "base_elevation": 3048,
        "vegetation": 0.48,
    },
    {
        "id": "AS-GHY",
        "name": "Guwahati foothills",
        "state": "Assam",
        "lat": 26.1445,
        "lon": 91.7362,
        "base_slope": 18,
        "base_elevation": 55,
        "vegetation": 0.55,
    },
    {
        "id": "AS-HFL",
        "name": "Haflong (Dima Hasao)",
        "state": "Assam",
        "lat": 25.1645,
        "lon": 93.0154,
        "base_slope": 36,
        "base_elevation": 680,
        "vegetation": 0.58,
    },
    {
        "id": "MN-IMP",
        "name": "Imphal valley rim",
        "state": "Manipur",
        "lat": 24.8170,
        "lon": 93.9368,
        "base_slope": 24,
        "base_elevation": 786,
        "vegetation": 0.60,
    },
    {
        "id": "MN-UKH",
        "name": "Ukhrul ridge",
        "state": "Manipur",
        "lat": 25.0484,
        "lon": 94.3600,
        "base_slope": 38,
        "base_elevation": 1662,
        "vegetation": 0.52,
    },
    {
        "id": "ML-SHL",
        "name": "Shillong plateau",
        "state": "Meghalaya",
        "lat": 25.5788,
        "lon": 91.8933,
        "base_slope": 28,
        "base_elevation": 1496,
        "vegetation": 0.64,
    },
    {
        "id": "ML-CHP",
        "name": "Cherrapunji escarpment",
        "state": "Meghalaya",
        "lat": 25.3000,
        "lon": 91.7000,
        "base_slope": 44,
        "base_elevation": 1484,
        "vegetation": 0.70,
        # One of the wettest places on Earth — rainfall will be higher here.
        "rain_multiplier": 1.8,
    },
    {
        "id": "MZ-AIZ",
        "name": "Aizawl slopes",
        "state": "Mizoram",
        "lat": 23.7271,
        "lon": 92.7176,
        "base_slope": 35,
        "base_elevation": 1132,
        "vegetation": 0.66,
    },
    {
        "id": "NL-KOH",
        "name": "Kohima ridge",
        "state": "Nagaland",
        "lat": 25.6751,
        "lon": 94.1086,
        "base_slope": 34,
        "base_elevation": 1444,
        "vegetation": 0.61,
    },
    {
        "id": "SK-GTK",
        "name": "Gangtok corridor",
        "state": "Sikkim",
        "lat": 27.3389,
        "lon": 88.6065,
        "base_slope": 40,
        "base_elevation": 1650,
        "vegetation": 0.57,
    },
    {
        "id": "TR-AGT",
        "name": "Agartala hills",
        "state": "Tripura",
        "lat": 23.8315,
        "lon": 91.2868,
        "base_slope": 16,
        "base_elevation": 16,
        "vegetation": 0.63,
    },
]

# Columns the AI model looks at. Each one is a "clue" about landslide risk.
FEATURE_COLUMNS = [
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "slope_deg",
    "soil_moisture",
    "elevation_m",
    "vegetation_cover",
    "prior_events",
]

# Probability thresholds → colour-coded warnings (simple NDMA-style idea).
ALERT_LEVELS = [
    {
        "name": "Low",
        "min": 0.0,
        "max": 0.25,
        "color": "#2f6f4e",
        "advice": "Routine monitoring. Roads are generally safe.",
    },
    {
        "name": "Moderate",
        "min": 0.25,
        "max": 0.50,
        "color": "#c9a227",
        "advice": "Watch slopes after rain. Avoid night travel on hill roads.",
    },
    {
        "name": "High",
        "min": 0.50,
        "max": 0.75,
        "color": "#d35400",
        "advice": "Restrict non-essential travel. Clear drains. Pre-position rescue teams.",
    },
    {
        "name": "Severe",
        "min": 0.75,
        "max": 1.01,
        "color": "#8b1e1e",
        "advice": "Issue public warning. Close vulnerable stretches. Prepare evacuation.",
    },
]


def station_by_id(station_id: str) -> dict:
    for station in STATIONS:
        if station["id"] == station_id:
            return station
    raise KeyError(f"Unknown station: {station_id}")
