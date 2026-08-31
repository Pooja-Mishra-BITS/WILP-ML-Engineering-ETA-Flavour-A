# ETA model comparison

| Model | MAE | RMSE | R2 | Features | Decision |
|---|---:|---:|---:|---|---|
| linear_regression | 3.8492 | 4.8231 | 0.9383 | numeric + one-hot categorical | Not selected |
| gradient_boosting | 3.6173 | 4.4615 | 0.9472 | numeric + one-hot categorical | Selected |

## Selection

The model with the lowest held-out RMSE was selected. The preprocessor is fit only on training rows and persisted inside artifacts/model.joblib.

## Limitations

The dataset is deterministic synthetic trip data. It demonstrates the engineering lifecycle but is not a substitute for a real fleet telemetry dataset.
