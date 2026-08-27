# ETA monitoring and drift report

{
  "baseline_size": 480,
  "drift_size": 120,
  "drift_methodology": "120 trips with longer distances, rush-hour traffic, adverse weather, and an additional delay component representing festival/seasonal congestion.",
  "metric": "PSI on trip_distance_km plus simulated RMSE/MAE",
  "psi": 3.248583,
  "drift_mae": 23.9021,
  "drift_rmse": 27.7416,
  "psi_threshold": 0.2,
  "rmse_threshold": 8.0,
  "production_feedback_rows": 0,
  "retraining_triggered": true,
  "action": "queue retraining with latest labelled trips",
  "workflow": [
    "monitor",
    "detect",
    "trigger",
    "train",
    "validate",
    "promote"
  ],
  "limitations": "PSI is sensitive to binning and sample size; simulated drift is not a substitute for live labelled feedback."
}
