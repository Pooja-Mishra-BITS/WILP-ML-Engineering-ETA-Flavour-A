# Delivery / Ride ETA Prediction

Machine Learning Engineering (PCAMZC412) mini-project to predict delivery or ride trip duration using trip distance, location, time, weather, and traffic.

## Project Overview

The project covers the complete ML workflow:

**Raw Data → Validation → Features → Training → Model → MLflow → FastAPI → Logging & Monitoring → Drift Detection → Retraining Decision**

The dataset is synthetic and is intended only for demonstrating the ML workflow end-to-end.

## Dataset

- **603 records** supplied in `data/raw/trips.csv`
- **600 valid records**
- **3 intentionally invalid records**
- Validation checks schema, GPS coordinates, distance, duration, time, weather, traffic, and timestamps
- Clean data: `data/processed/trips_clean.csv`
- Rejected rows: `data/processed/rejected_rows.jsonl`
- Dataset version: `data/VERSION`
- Dataset metadata and hashes: `data/manifest.json`

Training uses the existing raw CSV directly. It does not regenerate `data/raw/trips.csv`; validation writes the cleaned rows to `data/processed/trips_clean.csv` and records rejected rows in `data/processed/rejected_rows.jsonl`. The standalone generator remains available as `python -m pipeline.generate_data` when a new synthetic dataset is explicitly needed.

## Model

The model uses:
- Pickup and drop-off coordinates
- Trip distance
- Hour
- Weekday
- Weather
- Traffic level

Two regression models are compared:
- Linear Regression
- Gradient Boosting Regression

The model with the lowest test RMSE is selected.

The experiments record MAE, RMSE, R², model parameters, seed, dataset version, and train/test sizes.

The selected model and preprocessing pipeline are stored in:
- `artifacts/model.joblib`

Model version:
- `eta-gradient_boosting-v1`

Results are available in:
- `reports/model_comparison.md`
- `experiments/runs.jsonl`

## Project Structure

```text
api/                    FastAPI service (entrypoint: api.server:app)
artifacts/              Trained model (artifacts/model.joblib)
client/                 Simulated client traffic and feedback submission scripts
data/                   Raw, processed and versioned data
experiments/            Experiment records (runs.jsonl)
logs/                   Prediction and feedback logs
pipeline/               Data, training and monitoring scripts
reports/                Model comparison and monitoring/drift reports
submission/evidence/    Evidence instructions
tests/                  Automated tests (python -m unittest discover)
Dockerfile
params.yaml
requirements.txt
run.bat                 Build, train, test, and serve the full pipeline
run_client.bat          Simulate live traffic and generate monitoring dashboards
clean_demo.bat          Reset MLflow data and generated artifacts/reports/logs
README.md
