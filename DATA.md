# Data Sources and Data Processing

## 1. Dataset Source

This project uses the REFIT Electrical Load Measurements dataset, which contains household-level electricity measurements collected in UK homes.

**Official source:** https://pureportal.strath.ac.uk/en/datasets/refit-electrical-load-measurements/

The project uses two forms of the dataset:

- **Raw REFIT data:** Used for the data-quality investigation and cleaning exercise for House 1.
- **Cleaned REFIT data:** Used for washing-machine usage analysis across multiple households and appliance disaggregation modelling.

The dataset contains aggregate household electricity consumption and measurements from individual appliances.

## 2. Data Organization

The project organizes data into the following directories:

- `data/raw/` — Original raw House 1 CSV files.
- `data/cleaned/` — Official cleaned REFIT household CSV files.
- `data/processed/` — Cleaned, resampled, and modelling-ready datasets.
- `reports/` — Quality reports, analysis summaries, metrics, and visualizations.
- `notebooks/` — Python scripts used for inspection, preprocessing, analysis, and modelling.

The original downloaded dataset files are not intended to be committed to the public GitHub repository.

## 3. House 1 Raw Data Cleaning

House 1's two raw CSV files were inspected and combined for quality analysis.

The cleaning pipeline addresses:

- Exact duplicate rows.
- Repeated timestamps.
- Irregular sampling intervals.
- Negative and unusually high readings.
- Missing measurements and long outages.
- Conversion to one-minute resolution.

Repeated timestamps are consolidated using the median. Appliance readings above 4,000 W and negative readings are flagged as invalid and treated as missing. Aggregate readings above 4,000 W are flagged for quality review rather than automatically assumed to be valid.

The data is resampled to one-minute intervals. Interpolation is limited to gaps of at most two consecutive minutes, and longer missing periods are retained as missing and flagged.

These rules are project-specific quality-control decisions, not official REFIT dataset corrections.

## 4. Washing-Machine Analysis

Washing-machine channels were selected using the appliance mappings in the official REFIT readme. Four households were selected for detailed analysis:

| Household | Washing-machine channel |
|---|---|
| House 1 | Appliance 5 |
| House 2 | Appliance 2 |
| House 3 | Appliance 6 |
| House 5 | Appliance 3 |

The selected channels were resampled to one-minute resolution. Usage analysis includes active-minute counts, approximate energy, event duration, peak power, and time-of-day and weekday patterns.

A preliminary activity threshold of 10 W was used for usage analysis. Sustained flat readings lasting at least 120 minutes were flagged for review. Flagged values were retained in the processed data but excluded from selected activity-rate calculations.

The results are exploratory. In particular, House 5 contains many prolonged flat readings, which may affect event counts and usage estimates.

## 5. Appliance Disaggregation Data

House 1's aggregate household power is used as the input signal, and the washing-machine channel is the prediction target.

The modelling dataset contains one-minute records with valid aggregate and washing-machine measurements. Aggregate readings above 4,000 W are excluded from the modelling data. Time-history features are calculated from past observations, including lagged power and rolling averages.

The data is split chronologically into training and testing periods to reduce the risk of temporal leakage.

## 6. Important Limitations

- REFIT represents UK households; usage patterns may not generalize directly to Indian households.
- Missing readings and long outages can affect estimated energy and appliance activity.
- The official cleaned dataset has its own preprocessing decisions, which may differ from this project's raw-data cleaning rules.
- Appliance channel mappings must be checked against the official readme.
- Washing-machine event detection depends on the selected power threshold and inactivity-gap rule.
- The modelling results are based on one household's aggregate signal and washing-machine channel; performance across other households remains to be tested.
- Results at one-minute resolution do not establish performance at 15- or 30-minute smart-meter intervals.

## 7. Reproducibility

The Python scripts in `notebooks/` document the data inspection, cleaning, washing-machine analysis, and disaggregation experiments. Generated datasets and reports are stored under `data/processed/` and `reports/`.

The public repository should include the code and documentation, but not the full REFIT dataset. Users should obtain the data from the official REFIT source and place the required files in the expected directories.
