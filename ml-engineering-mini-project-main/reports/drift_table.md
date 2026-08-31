# Client traffic drift report

Baseline rows: 600  |  Live requests analysed: 150

## Numeric feature drift (covariate/data drift)

| Feature | Baseline Mean | Live Mean | Baseline Std | Live Std | PSI | Mean shift (z) | Drift? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| pickup_lat | 40.7243 | 40.7298 | 0.0722 | 0.0738 | 0.0345 | 0.0764 | no |
| pickup_lon | -73.9278 | -73.9364 | 0.0718 | 0.0749 | 0.0561 | 0.1197 | no |
| dropoff_lat | 40.7226 | 40.7134 | 0.0737 | 0.066 | 0.2436 | 0.1252 | YES |
| dropoff_lon | -73.9222 | -73.9368 | 0.0731 | 0.0714 | 0.1069 | 0.1995 | no |
| trip_distance_km | 15.023 | 15.302 | 7.9032 | 8.0775 | 0.0675 | 0.0353 | no |
| hour | 11.52 | 11.3133 | 6.7924 | 7.1992 | 0.022 | 0.0304 | no |
| weekday | 3.16 | 2.8267 | 1.9827 | 2.0058 | 0.0503 | 0.1681 | no |

## Categorical feature drift

| Feature | Total Variation Distance | Drift? |
|---|---:|:---:|
| weather | 0.235 | YES |
| traffic_level | 0.0267 | no |

## Concept drift (proxy, no ground truth yet)

```json
{
  "metric": "PSI(train target vs live predicted eta) - proxy for concept drift; true concept drift needs labelled live outcomes (logs/feedback.jsonl)",
  "baseline_target_mean": 51.1786,
  "live_predicted_mean": 49.4527,
  "psi": 0.4279,
  "drift": true,
  "ground_truth_available": false
}
```

Thresholds: PSI >= 0.2 | mean-shift z >= 2.0 | TVD >= 0.15
