
from pathlib import Path
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"

path = REPORT_DIR / "disaggregation_feature_predictions.csv"
df = pd.read_csv(path)

# Define actual and predicted activity using a 10 W threshold.
# This threshold is an analytical choice for this experiment.
actual_active = df["actual_w"] > 10
predicted_active = df["predicted_w"] > 10

tn, fp, fn, tp = confusion_matrix(
    actual_active,
    predicted_active,
    labels=[False, True],
).ravel()

results = {
    "threshold_w": 10,
    "true_positives": int(tp),
    "false_positives": int(fp),
    "true_negatives": int(tn),
    "false_negatives": int(fn),
    "precision": round(
        float(precision_score(
            actual_active, predicted_active, zero_division=0
        )), 4
    ),
    "recall": round(
        float(recall_score(
            actual_active, predicted_active, zero_division=0
        )), 4
    ),
    "f1_score": round(
        float(f1_score(
            actual_active, predicted_active, zero_division=0
        )), 4
    ),
}

print("ACTIVITY DETECTION EVALUATION")
print("=" * 45)
for key, value in results.items():
    print(f"{key}: {value}")

print("\nClassification report:")
print(classification_report(
    actual_active,
    predicted_active,
    target_names=["Inactive", "Active"],
    zero_division=0,
))

print("\nInterpretation:")
print("False positives are inactive minutes incorrectly predicted as active.")
print("False negatives are active minutes the model failed to detect.")
