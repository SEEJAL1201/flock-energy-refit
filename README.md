# REFIT Data Cleaning and Appliance Disaggregation

A Python-based project for cleaning household electricity measurements, analyzing washing-machine usage, and estimating appliance-level power consumption from aggregate household electricity data.

## Project Overview

Smart-meter data contains missing readings, duplicate timestamps, irregular sampling intervals, sensor anomalies, and long outages. These issues can affect appliance-level analysis and energy estimates.

This project investigates these challenges using the REFIT Electrical Load Measurements dataset. It covers four main areas:

1. Raw-data quality assessment and cleaning.
2. Washing-machine usage analysis across multiple households.
3. Washing-machine power estimation from aggregate household consumption.
4. Recommendations for appliance monitoring and deployment.

## Objectives

- Identify and document data-quality problems in raw electricity measurements.
- Develop a reproducible cleaning and one-minute resampling pipeline.
- Compare washing-machine activity across selected households.
- Build an explainable baseline and machine-learning model for appliance disaggregation.
- Evaluate model errors and identify limitations relevant to deployment.

## Dataset

The project uses the publicly available [REFIT Electrical Load Measurements dataset](https://pureportal.strath.ac.uk/en/datasets/refit-electrical-load-measurements/).

REFIT contains aggregate electricity measurements and individual appliance readings from UK households.

The analysis includes:

- **House 1 raw data:** detailed data-quality investigation and cleaning.
- **Houses 1, 2, 3, and 5:** washing-machine usage analysis.
- **House 1:** washing-machine power estimation from aggregate household power.

The full dataset is not included in this repository. See `DATA.md` for source links, channel mappings, processing rules, and limitations.

## Methodology

### 1. Data Cleaning

The raw House 1 files are inspected for duplicate records, repeated timestamps, missing readings, irregular intervals, negative values, and unusually high power readings.

The pipeline consolidates repeated timestamps, flags questionable readings, resamples measurements to one-minute intervals, and interpolates only short gaps. Longer outages remain identified as missing.

### 2. Washing-Machine Usage Analysis

Washing-machine channels are selected using the official REFIT readme. The analysis examines active minutes, approximate energy consumption, peak power, event duration, and weekday and hourly patterns.

A preliminary activity threshold of 10 W is used in the exploratory analysis. Sustained flat readings are flagged because they can distort usage estimates and event detection.

### 3. Appliance Disaggregation

A zero-power baseline and two Random Forest approaches are compared:

- **Aggregate-only model:** uses current aggregate household power.
- **Time-history model:** adds lagged power, rolling averages, and time-related features.

A chronological training/testing split is used. Performance is evaluated using mean absolute error (MAE), root mean squared error (RMSE), and coefficient of determination (\(R^2\)). Appliance activity detection is evaluated separately because accurate power estimation does not necessarily imply accurate event detection.

## Preliminary Results

The fair comparison uses the same eligible records and chronological test period for all three approaches.

| Model | MAE (W) | RMSE (W) | R² |
|---|---:|---:|---:|
| Zero-power baseline | 9.006 | 129.344 | -0.0049 |
| Random Forest — aggregate only | 9.837 | 90.856 | 0.5042 |
| Random Forest — time history | 7.476 | 82.097 | 0.5952 |

The time-history model reduces MAE by approximately 24% and RMSE by approximately 9.6% compared with the aggregate-only Random Forest on the same test records.

However, washing-machine activity detection remains challenging. At a 10 W prediction threshold, recall is approximately 0.866, while precision is approximately 0.310. This indicates that the model detects many actual active minutes but also generates false-positive activity predictions.

These are preliminary results from House 1, not evidence of general performance across all households. See `RESULTS.md` for detailed metrics, usage analysis, and caveats.

## Repository Structure

```text
flock-energy-refit/
├── data/
│   ├── raw/
│   ├── cleaned/
│   └── processed/
├── notebooks/
│   ├── inspect_archives.py
│   ├── clean_house1.py
│   ├── analyze_washing_machine_usage.py
│   ├── analyze_usage_patterns.py
│   ├── prepare_disaggregation_data.py
│   ├── fair_model_comparison.py
│   └── other analysis scripts
├── reports/
├── README.md
├── DATA.md
├── RESULTS.md
└── Recommendation.md
```

The directory listing is representative; retain the actual scripts and report files present in your repository.

## How to Run

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

Create a `requirements.txt` containing the packages used by your scripts. At minimum, the workflow uses common data-science packages such as:

```text
pandas
numpy
matplotlib
scikit-learn
```

Install them with:

```powershell
pip install -r requirements.txt
```

Add any other packages imported by your scripts to `requirements.txt`.

### 3. Obtain the dataset

Download the required raw and cleaned files from the official REFIT source. Place them in the corresponding `data/raw/` and `data/cleaned/` directories.

Check the input filenames and paths in each script before running it.

### 4. Run the analysis

Run the scripts from the project root in the appropriate order:

1. Inspect and clean House 1 raw data.
2. Validate the cleaning output.
3. Analyze washing-machine usage.
4. Prepare the disaggregation dataset.
5. Train and evaluate the models.
6. Generate the final reports and plots.

For example:

```powershell
python notebooks/clean_house1.py
python notebooks/validate_cleaning.py
python notebooks/analyze_washing_machine_usage.py
python notebooks/prepare_disaggregation_data.py
python notebooks/fair_model_comparison.py
```

Some scripts depend on outputs generated by earlier scripts. Follow the input paths and dependencies defined in your local files.

## Limitations

- REFIT represents UK households, so results may not generalize directly to Indian homes.
- Missing data, outages, and unusual sensor readings can affect results.
- Flat appliance readings can distort estimated usage and event durations.
- The disaggregation experiment uses one household and one appliance channel.
- One-minute results do not establish performance at 15- or 30-minute sampling intervals.
- Further validation across households and appliance types is needed before deployment.

## Documentation

- `DATA.md` — dataset sources, channel mappings, and preprocessing.
- `RESULTS.md` — data-quality findings, usage analysis, and model evaluation.
- `Recommendation.md` — deployment recommendations, measurement plan, and limitations.

## Acknowledgement

The REFIT Electrical Load Measurements dataset is provided by its original research team. Please consult the official dataset page and accompanying documentation for dataset terms, attribution, and usage conditions.
