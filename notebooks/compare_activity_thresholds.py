
from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / "reports" / "disaggregation_feature_predictions.csv"

df = pd.read_csv(path)
actual_active = df["actual_w"] > 10

print("ACTIVITY THRESHOLD COMPARISON")
print("=" * 75)
print(
    f"{'Threshold':>10} {'Precision':>12} {'Recall':>10} "
    f"{'F1-score':>10} {'False positives':>18} {'Detected active':>17}"
)

for threshold in [10, 25, 50, 100, 200]:
    predicted_active = df["predicted_w"] > threshold

    precision = precision_score(
        actual_active, predicted_active, zero_division=0
    )
    recall = recall_score(
        actual_active, predicted_active, zero_division=0
    )
    f1 = f1_score(
        actual_active, predicted_active, zero_division=0
    )

    false_positives = int((predicted_active & ~actual_active).sum())
    detected_active = int((predicted_active & actual_active).sum())

    print(
        f"{threshold:>10} "
        f"{precision:>12.4f} "
        f"{recall:>10.4f} "
        f"{f1:>10.4f} "
        f"{false_positives:>18,} "
        f"{detected_active:>17,}"
    )

print("\nNote: actual activity is consistently defined as actual power >10 W.")
