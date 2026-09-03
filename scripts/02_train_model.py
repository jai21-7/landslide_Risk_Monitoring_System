"""Step 3 in the learning path: train the Random Forest and print a scorecard."""

from ner_landslide.data import load_history
from ner_landslide.model import train_model

if __name__ == "__main__":
    metrics = train_model(load_history())
    print("Accuracy:", round(metrics["accuracy"], 3))
    print("ROC-AUC:", round(metrics["roc_auc"], 3))
    print("Rows:", metrics["n_rows"])
    print("Feature importance (higher = more useful):")
    for name, score in sorted(metrics["feature_importance"].items(), key=lambda x: -x[1]):
        print(f"  {name:20s} {score:.3f}")
