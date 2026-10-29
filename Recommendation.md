# Recommendation: Appliance-Level Energy Monitoring

## 1. Recommendation

For an energy-monitoring system, I recommend using aggregate household power together with recent power history to estimate washing-machine consumption. In the REFIT House 1 experiment, a Random Forest model using aggregate power, lagged readings, rolling averages, hour of day and day of week achieved an MAE of 7.476 W, RMSE of 82.097 W and R² of 0.5952 on a chronological test set.

These results support further investigation of time-history features for appliance disaggregation. However, the model should not yet be treated as a reliable standalone washing-machine detector because its active-period errors and false-positive activity predictions remain substantial.

## 2. Proposed Measurement Plan

A practical deployment should collect the following measurements:

- Aggregate household electricity consumption at one-minute resolution or finer.
- Washing-machine-level power measurements for a representative subset of households to provide reference labels.
- Timestamped readings with consistent clock synchronization.
- Data-quality indicators for missing intervals, implausible power values and prolonged constant readings.
- Measurements covering weekdays, weekends, different seasons and a variety of washing-machine types.

For initial validation, collect aggregate and appliance-level readings simultaneously. Use the appliance-level measurements as ground truth, then compare predicted and measured washing-machine power over a held-out period.

## 3. Data Quality and Validation

The REFIT House 1 raw data contained duplicate timestamps, irregular intervals and extreme readings. The cleaning workflow removed exact duplicate rows, consolidated repeated timestamps, resampled data to one-minute intervals, interpolated only short gaps and flagged longer outages and suspicious power readings.

The official cleaned REFIT dataset also contains long periods of constant washing-machine readings in House 5. These were flagged for investigation rather than automatically removed. Such periods illustrate why sensor quality checks are important before estimating appliance usage.

Future deployment should retain quality flags and report metrics both on all eligible observations and on actual appliance-active periods.

## 4. Limitations

- The model was developed using REFIT data collected in UK homes, so performance may differ in Indian homes because of appliance types, operating practices, voltage conditions and household load profiles.
- The washing-machine target is highly imbalanced: most minute-level readings are zero.
- The model's aggregate-power input can be confused by other appliances operating at similar power levels.
- The current activity threshold comparison shows a trade-off between precision and recall. The selected threshold should be validated against deployment requirements.
- Long constant readings and missing intervals may affect usage statistics and event detection.
- Performance at one-minute resolution does not establish performance at 15- or 30-minute resolution. Coarser readings can hide short power cycles and reduce the ability to separate appliances.
- Results from one household do not establish generalization across all households or appliance models.

## 5. Transfer to Indian Homes

Before deployment in India, the model should be tested on locally collected household data. Collect simultaneous aggregate and washing-machine measurements from homes with different appliance models and usage patterns. Evaluate performance separately for each household and appliance type.

If only 15- or 30-minute smart-meter data are available, retrain and evaluate the model at that resolution instead of assuming that the one-minute results will transfer directly.

## 6. Conclusion

The experiment indicates that adding recent aggregate-power history and time features improves washing-machine power estimation compared with an aggregate-only Random Forest under the same chronological test split. However, further validation is needed to improve active-period estimation, reduce false positives, investigate sensor anomalies and assess transfer to new households.

The recommended next step is a controlled pilot using synchronized aggregate and appliance-level measurements, followed by household-level validation before operational deployment.