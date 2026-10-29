
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

df = pd.read_csv(
    DATA_DIR / "house1_disaggregation_1min.csv",
    parse_dates=["Time"],
)
df = df.sort_values("Time").drop_duplicates("Time").reset_index(drop=True)

# Flag suspicious readings and preserve their timestamps.
df.loc[df["Aggregate"] > 4000, "Aggregate"] = np.nan

# Do not interpolate long gaps. Keep only rows with valid input and target.
df["Aggregate"] = pd.to_numeric(df["Aggregate"], errors="coerce")
df["Appliance5"] = pd.to_numeric(df["Appliance5"], errors="coerce")

# Create lagged and rolling features using past readings only.
for lag in [1, 5, 15]:
    df[f"aggregate_lag_{lag}"] = df["Aggregate"].shift(lag)

df["aggregate_rolling_mean_5"] = (
    df["Aggregate"].shift(1).rolling(5, min_periods=5).mean()
)
df["aggregate_rolling_mean_15"] = (
    df["Aggregate"].shift(1).rolling(15, min_periods=15).mean()
)

# Time features can capture daily and weekly usage patterns.
df["hour"] = df["Time"].dt.hour
df["day_of_week"] = df["Time"].dt.dayofweek

features = [
    "Aggregate",
    "aggregate_lag_1",
    "aggregate_lag_5",
    "aggregate_lag_15",
    "aggregate_rolling_mean_5",
    "aggregate_rolling_mean_15",
    "hour",
    "day_of_week",
]

# Keep a chronological split; no random shuffle.
split_time = df["Time"].iloc[int(len(df) * 0.8)]

train = df[df["Time"] < split_time].copy()
test = df[df["Time"] >= split_time].copy()

train = train.dropna(subset=features + ["Appliance5"])
test = test.dropna(subset=features + ["Appliance5"])

X_train = train[features]
y_train = train["Appliance5"]
X_test = test[features]
y_test = test["Appliance5"]

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=14,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)
predictions = np.maximum(model.predict(X_test), 0)

def metrics(y, pred):
    return {
        "samples": int(len(y)),
        "MAE_W": round(float(mean_absolute_error(y, pred)), 3),
        "RMSE_W": round(float(np.sqrt(mean_squared_error(y, pred))), 3),
        "R2": round(float(r2_score(y, pred)), 4),
    }

active = y_test > 10

results = {
    "train_rows": int(len(train)),
    "test_rows": int(len(test)),
    "train_start": str(train["Time"].min()),
    "train_end": str(train["Time"].max()),
    "test_start": str(test["Time"].min()),
    "test_end": str(test["Time"].max()),
    "features": features,
    "all_test_minutes": metrics(y_test, predictions),
    "active_minutes_over_10W": metrics(
        y_test[active], predictions[active]
    ),
    "actual_active_minutes": int(active.sum()),
    "predicted_active_minutes": int((predictions > 10).sum()),
    "feature_importance": {
        name: round(float(value), 5)
        for name, value in zip(features, model.feature_importances_)
    },
}

(REPORT_DIR / "disaggregation_feature_model_results.json").write_text(
    json.dumps(results, indent=2)
)

pd.DataFrame({
    "Time": test["Time"].values,
    "actual_w": y_test.values,
    "predicted_w": predictions,
}).to_csv(
    REPORT_DIR / "disaggregation_feature_predictions.csv",
    index=False,
)

plt.figure(figsize=(14, 5))
sample_size = min(7 * 24 * 60, len(test))
plt.plot(test["Time"].iloc[:sample_size], y_test.iloc[:sample_size],
         label="Actual", linewidth=0.8)
plt.plot(test["Time"].iloc[:sample_size], predictions[:sample_size],
         label="Predicted", linewidth=0.8)
plt.xlabel("Time")
plt.ylabel("Power (W)")
plt.title("Washing-Machine Disaggregation with Time-History Features")
plt.legend()
plt.tight_layout()
plt.savefig(
    REPORT_DIR / "disaggregation_feature_model_plot.png",
    dpi=150,
)
plt.close()

print("FEATURE-BASED MODEL RESULTS")
print("=" * 50)
print(json.dumps(results, indent=2))
print("\nResults saved in reports/")
