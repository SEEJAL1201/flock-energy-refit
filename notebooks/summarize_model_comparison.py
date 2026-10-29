
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"

first_path = REPORT_DIR / "disaggregation_model_results.json"
feature_path = REPORT_DIR / "disaggregation_feature_model_results.json"

with open(first_path, encoding="utf-8") as f:
    first = json.load(f)

with open(feature_path, encoding="utf-8") as f:
    improved = json.load(f)

comparison = pd.DataFrame([
    {
        "model": "Zero baseline",
        "test_rows": first["test_rows"],
        "MAE_W": first["baseline"]["MAE_W"],
        "RMSE_W": first["baseline"]["RMSE_W"],
        "R2": first["baseline"]["R2"],
        "features": "Always predict zero",
    },
    {
        "model": "Random Forest: aggregate only",
        "test_rows": first["test_rows"],
        "MAE_W": first["random_forest"]["MAE_W"],
        "RMSE_W": first["random_forest"]["RMSE_W"],
        "R2": first["random_forest"]["R2"],
        "features": "Aggregate power",
    },
    {
        "model": "Random Forest: time-history features",
        "test_rows": improved["test_rows"],
        "MAE_W": improved["all_test_minutes"]["MAE_W"],
        "RMSE_W": improved["all_test_minutes"]["RMSE_W"],
        "R2": improved["all_test_minutes"]["R2"],
        "features": "Aggregate, lags, rolling means, hour, weekday",
    },
])

output = REPORT_DIR / "model_comparison.csv"
comparison.to_csv(output, index=False)

print("MODEL COMPARISON")
print("=" * 80)
print(comparison.to_string(index=False))
print("\nSaved:", output)
print(
    "\nNote: the first two models and the feature model do not use "
    "identical filtering, so compare their scores cautiously."
)
