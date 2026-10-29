# Results

## 1. House 1 Data Cleaning

The raw House 1 data contained 8,518,763 rows across two source files. The cleaning workflow removed 595,940 exact duplicate rows, consolidated repeated timestamps, and resampled the data to one-minute intervals.

| Data-quality measure | Result |
|---|---:|
| Input rows | 8,518,763 |
| Exact duplicate rows removed | 595,940 |
| Repeated timestamp groups identified | 162,394 |
| Original intervals exceeding 60 seconds | 4,037 |
| Output one-minute rows | 920,031 |
| Minutes flagged as long outages | 113,555 |
| Aggregate extreme readings above 4,000 W | 37,948 source readings |

The cleaned dataset contains no duplicate minute timestamps or irregular minute intervals. Short gaps were interpolated under the implemented policy, while longer outages and suspicious readings were flagged.

## 2. Washing-Machine Usage Across Four Households

The following summary was calculated using a 10 W activity threshold.

| Household | Washing-machine channel | Active minutes | Active percentage | Approximate energy (kWh) | Preliminary events |
|---|---|---:|---:|---:|---:|
| House 1 | Appliance5 | 14,924 | 1.86% | 145.128 | 408 |
| House 2 | Appliance2 | 30,996 | 4.63% | 201.975 | 312 |
| House 3 | Appliance6 | 42,034 | 5.36% | 378.247 | 670 |
| House 5 | Appliance3 | 67,655 | 7.99% | 444.917 | 881 |

These are preliminary usage statistics. Energy totals include readings that may require further quality review, and the event counts are not confirmed washing cycles.

## 3. Usage Patterns

The average daily activity rates varied by household and day of the week.

| Household | Highest activity day | Activity rate |
|---|---|---:|
| House 1 | Wednesday | 2.53% |
| House 2 | Monday | 6.56% |
| House 3 | Tuesday | 8.14% |
| House 5 | Saturday | 14.67% |

House 5 showed a substantially higher activity rate on Saturday than on Tuesday. However, House 5 also contained 19,302 minutes flagged for sustained constant-power readings. Its weekday pattern should therefore be interpreted cautiously.

## 4. Appliance Disaggregation

House 1 was used for the initial washing-machine disaggregation experiments. The target was Appliance5 power, and aggregate household power was used as the main input.

The final fair comparison used 623,098 training rows and 155,775 test rows, with the test period running from 21 February 2015 to 10 July 2015.

| Model | MAE (W) | RMSE (W) | R² |
|---|---:|---:|---:|
| Zero baseline | 9.006 | 129.344 | -0.0049 |
| Random Forest — aggregate only | 9.837 | 90.856 | 0.5042 |
| Random Forest — time-history features | 7.476 | 82.097 | 0.5952 |

The time-history model used aggregate power, lagged aggregate readings, rolling averages, hour of day and day of week. It produced the lowest MAE and RMSE and the highest R² in this comparison.

Compared with the aggregate-only Random Forest, the time-history model reduced MAE by approximately 24.0% and RMSE by approximately 9.6%.

## 5. Activity Detection

Using a 10 W actual-activity definition and a 10 W prediction threshold, the time-history model achieved:

| Metric | Result |
|---|---:|
| Precision | 0.3097 |
| Recall | 0.8662 |
| F1-score | 0.4563 |
| False positives | 5,063 |
| False negatives | 351 |

A threshold comparison found the highest F1-score among the tested prediction thresholds at 50 W:

| Prediction threshold | Precision | Recall | F1-score |
|---|---:|---:|---:|
| 10 W | 0.3097 | 0.8662 | 0.4563 |
| 25 W | 0.4084 | 0.7629 | 0.5320 |
| 50 W | 0.4948 | 0.6355 | 0.5564 |
| 100 W | 0.5658 | 0.4441 | 0.4977 |
| 200 W | 0.6046 | 0.2402 | 0.3438 |

The 50 W threshold provided the best F1-score among these five choices. It reduced false positives compared with the 10 W prediction threshold, but also reduced recall. Actual activity remained defined as measured power above 10 W.

## 6. Limitations

- The target contains many zero-power readings, which affects overall error metrics.
- Active-period prediction errors remain substantial.
- Flat readings and missing data may affect event detection and energy estimates.
- Results from one household do not establish generalization to other homes.
- Performance at one-minute resolution does not establish performance at 15- or 30-minute resolution.

The results support further investigation of time-history features for appliance disaggregation, but additional validation is required before practical deployment.