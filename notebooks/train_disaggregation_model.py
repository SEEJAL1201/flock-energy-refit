
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "house1_disaggregation_1min.csv"

df = pd.read_csv(INPUT_FILE, parse_dates=["Time"])
df = df.sort_values("Time").reset_index(drop=True)

# Keep the target and aggregate input.
df = df[["Time", "Aggregate", "Appliance5"]].dropna()

# Chronological 80/20 split.
split_index = int(len(df) * 0.8)
train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

X_train = train[["Aggregate"]]
y_train = train["Appliance5"]
X_test = test[["Aggregate"]]
y_test = test["Appliance5"]

# Baseline: always predict zero washing-machine power.
baseline_predictions = np.zeros(len(test))

# Initial explainable model using aggregate power only.
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)
predictions = np.maximum(model.predict(X_test), 0)

def calculate_metrics(actual, predicted):
    return {
        "MAE_W": round(float(mean_absolute_error(actual, predicted)), 3),
        "RMSE_W": round(float(np.sqrt(mean_squared_error(actual, predicted))), 3),
        "R2": round(float(r2_score(actual, predicted)), 4),
    }

results = {
    "train_rows": int(len(train)),
    "test_rows": int(len(test)),
    "train_start": str(train["Time"].min()),
    "train_end": str(train["Time"].max()),
    "test_start": str(test["Time"].min()),
    "test_end": str(test["Time"].max()),
    "target_zero_percentage_train": round(
        100 * (y_train == 0).mean(), 2
    ),
    "target_zero_percentage_test": round(
        100 * (y_test == 0).mean(), 2
    ),
    "baseline": calculate_metrics(y_test, baseline_predictions),
    "random_forest": calculate_metrics(y_test, predictions),
}

report_file = REPORT_DIR / "disaggregation_model_results.json"
report_file.write_text(json.dumps(results, indent=2))

prediction_file = REPORT_DIR / "disaggregation_test_predictions.csv"
pd.DataFrame({
    "Time": test["Time"].values,
    "actual_w": y_test.values,
    "predicted_w": predictions,
    "aggregate_w": X_test["Aggregate"].values,
}).to_csv(prediction_file, index=False)

# Plot a sample of the test period.
sample_size = min(7 * 24 * 60, len(test))
plt.figure(figsize=(14, 5))
plt.plot(
    test["Time"].iloc[:sample_size],
    y_test.iloc[:sample_size],
    label="Actual washing-machine power",
    linewidth=0.8,
)
plt.plot(
    test["Time"].iloc[:sample_size],
    predictions[:sample_size],
    label="Predicted washing-machine power",
    linewidth=0.8,
)
plt.xlabel("Time")
plt.ylabel("Power (W)")
plt.title("House 1: Actual vs Predicted Washing-Machine Power")
plt.legend()
plt.tight_layout()
plot_file = REPORT_DIR / "disaggregation_actual_vs_predicted.png"
plt.savefig(plot_file, dpi=150)
plt.close()

print("DISAGGREGATION MODEL RESULTS")
print("=" * 50)
print(json.dumps(results, indent=2))
print("\nResults:", report_file)
print("Predictions:", prediction_file)
print("Plot:", plot_file)
