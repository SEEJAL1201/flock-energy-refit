
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"

path = REPORT_DIR / "disaggregation_test_predictions.csv"
df = pd.read_csv(path, parse_dates=["Time"])

actual = df["actual_w"]
predicted = df["predicted_w"]

def metrics(y_true, y_pred):
    if len(y_true) == 0:
        return {
            "samples": 0,
            "MAE_W": None,
            "RMSE_W": None,
            "R2": None,
        }

    result = {
        "samples": int(len(y_true)),
        "MAE_W": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "RMSE_W": round(
            float(np.sqrt(mean_squared_error(y_true, y_pred))), 3
        ),
        "R2": None,
    }

    if len(y_true) >= 2 and y_true.nunique() > 1:
        result["R2"] = round(float(r2_score(y_true, y_pred)), 4)

    return result

active = actual > 10
inactive = ~active

results = {
    "all_test_minutes": metrics(actual, predicted),
    "actual_active_minutes_over_10W": metrics(
        actual[active], predicted[active]
    ),
    "actual_inactive_minutes_at_or_below_10W": metrics(
        actual[inactive], predicted[inactive]
    ),
    "active_test_minutes": int(active.sum()),
    "active_test_percentage": round(100 * active.mean(), 2),
    "predicted_active_minutes_over_10W": int((predicted > 10).sum()),
}

output = REPORT_DIR / "disaggregation_active_evaluation.json"
output.write_text(json.dumps(results, indent=2))

print("ACTIVE-PERIOD EVALUATION")
print("=" * 50)
print(json.dumps(results, indent=2))
print("\nSaved:", output)
