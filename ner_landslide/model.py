"""
STEP 3 — Train a small AI model.

We use Random Forest: many simple "yes/no trees" that vote.
It is a good first model because:
  - it handles mixed numbers (rain, slope, vegetation)
  - it can tell you which clues mattered most
  - it does not need a GPU

After training, we save the model to models/landslide_model.pkl
so the website can load it in milliseconds.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from ner_landslide.config import FEATURE_COLUMNS, MODEL_DIR, MODEL_PATH
from ner_landslide.data import features_frame, load_history


def _positive_proba(model: RandomForestClassifier, X: pd.DataFrame) -> np.ndarray:
    """Chance of class 1 (landslide). Safe if a tiny dataset has only one class."""
    raw = model.predict_proba(X)
    classes = list(model.classes_)
    if 1 not in classes:
        return np.zeros(len(X))
    return raw[:, classes.index(1)]


def train_model(df: pd.DataFrame | None = None, seed: int = 42) -> dict:
    df = df if df is not None else load_history()
    X = features_frame(df)
    y = df["landslide_occurred"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=160,
        max_depth=10,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    proba = _positive_proba(model, X_test)
    preds = (proba >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "positive_rate": float(y.mean()),
        "n_rows": int(len(df)),
        "report": classification_report(y_test, preds, output_dict=True),
        "feature_importance": {
            name: float(score)
            for name, score in zip(FEATURE_COLUMNS, model.feature_importances_)
        },
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLUMNS, "metrics": metrics}, MODEL_PATH)
    return metrics


def load_bundle() -> dict:
    if not MODEL_PATH.exists():
        train_model()
    return joblib.load(MODEL_PATH)


def predict_risk(rows: pd.DataFrame) -> pd.DataFrame:
    """Add probability + predicted class to a table of station readings."""
    bundle = load_bundle()
    model = bundle["model"]
    X = rows[FEATURE_COLUMNS]
    out = rows.copy()
    out["risk_probability"] = np.round(_positive_proba(model, X), 3)
    out["predicted_event"] = (out["risk_probability"] >= 0.5).astype(int)
    return out


def model_path() -> Path:
    return MODEL_PATH
