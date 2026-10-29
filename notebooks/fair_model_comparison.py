
from pathlib import Path
import json
import numpy as np
import pandas as pd

from sklearn.dummy import DummyRegressor
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

df["Aggregate"] = pd.to_numeric(df["Aggregate"], errors="coerce")
df["Appliance5"] = pd.to_numeric(df["Appliance5"], errors="coerce")

# Apply the same aggregate quality rule to every model.
df.loc[df["Aggregate"] > 4000, "Aggregate"] = np.nan

# Create past-only features.
for lag in [1, 5, 15]:
    df[f"aggregate_lag_{lag}"] = df["Aggregate"].shift(lag)

df["aggregate_rolling_mean_5"] = (
    df["Aggregate"].shift(1).rolling(5, min_periods=5).mean()
)
df["aggregate_rolling_mean_15"] = (
    df["Aggregate"].shift(1).rolling(15, min_periods=15).mean()
)
df["hour"] = df["Time"].dt.hour
df["day_of_week"] = df["Time"].dt.day_of_week

feature_cols = [
    "Aggregate",
    "aggregate_lag_1",
    "aggregate_lag_5",
    "aggregate_lag_15",
    "aggregate_rolling_mean_5",
    "aggregate_rolling_mean_15",
    "hour",
    "day_of_week",
]

# All models use the same complete rows, so the comparison is fair.
required = ["Aggregate", "Appliance5"] + feature_cols[1:6]
df = df.dropna(subset=required).reset_index(drop=True)

split = int(len(df) * 0.8)
train = df.iloc[:split].copy()
test = df.iloc[split:].copy()

y_train = train["Appliance5"]
y_test = test["Appliance5"]

models = {
    "Zero baseline": None,
    "Random Forest aggregate only": ["Aggregate"],
    "Random Forest time-history": feature_cols,
}

results = []

for name, features in models.items():
    if features is None:
        model = DummyRegressor(strategy="constant", constant=0)
        model.fit(np.zeros((len(train), 1)), y_train)
        pred = model.predict(np.zeros((len(test), 1)))
    else:
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=14 if len(features) > 1 else 12,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(train[features], y_train)
        pred = np.maximum(model.predict(test[features]), 0)

    results.append({
        "model": name,
        "train_rows": len(train),
        "test_rows": len(test),
        "MAE_W": round(float(mean_absolute_error(y_test, pred)), 3),
        "RMSE_W": round(float(np.sqrt(mean_squared_error(y_test, pred))), 3),
        "R2": round(float(r2_score(y_test, pred)), 4),
    })

comparison = pd.DataFrame(results)
comparison.to_csv(REPORT_DIR / "fair_model_comparison.csv", index=False)

print("FAIR MODEL COMPARISON — IDENTICAL TEST ROWS")
print("=" * 65)
print(comparison.to_string(index=False))
print("\nSaved: reports/fair_model_comparison.csv")
print("Test period:", test["Time"].min(), "to", test["Time"].max())
