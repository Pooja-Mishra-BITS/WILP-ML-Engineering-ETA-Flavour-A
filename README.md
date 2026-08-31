# Delivery / Ride ETA Prediction
# Machine Learning Engineering (PCAMZC412) mini-project to predict delivery or ride trip duration using trip distance, location, time, weather, and traffic.

# Project Overview

# The project covers the complete ML workflow:
Raw Data → Validation → Features → Training → Model → MLflow → FastAPI → Logging & Monitoring → Drift Detection → Retraining Decision
The dataset is synthetic and is intended only for demonstrating the ML workflow end-to-end.
Dataset
603 records supplied in data/raw/trips.csv
600 valid records
3 intentionally invalid records
Validation checks schema, GPS coordinates, distance, duration, time, weather, traffic, and timestamps
Clean data: data/processed/trips_clean.csv
Rejected rows: data/processed/rejected_rows.jsonl
Dataset version: data/VERSION
Dataset metadata and hashes: data/manifest.json
Training uses the existing raw CSV directly. It does not regeneratedata/raw/trips.csv; validation writes the cleaned rows todata/processed/trips_clean.csv and records rejected rows indata/processed/rejected_rows.jsonl. The standalone generator remains available as python -m pipeline.generate_data when a new synthetic dataset is explicitly needed.
Model
The model uses:
Pickup and drop-off coordinates
Trip distance
Hour
Weekday
Weather
Traffic level
Two regression models are compared:
Linear Regression
Gradient Boosting Regression
The model with the lowest test RMSE is selected.
The experiments record MAE, RMSE, R², model parameters, seed, dataset version, and train/test sizes.
The selected model and preprocessing pipeline are stored in:
artifacts/model.joblib
Model version:
eta-gradient_boosting-v1
Results are available in:
reports/model_comparison.md
experiments/runs.jsonl
Project Structure
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
Requirements
Tested against Python 3.11/3.12. Key pinned dependencies (requirements.txt):
Package
Version
fastapi
0.115.6
uvicorn[standard]
0.34.0
scikit-learn
1.6.1
mlflow
2.20.2
joblib
1.4.2
PyYAML
6.0.2
httpx
0.28.1
pandas
2.2.3

Running the project via the provided scripts also requires Docker Desktop (the scripts are Windows .bat files that call docker build /docker run).
Running the Project
1. Train, test, and start the API
run.bat
This builds the Docker image, starts an MLflow container, trains the model (python -m pipeline.train), runs monitoring (python -m pipeline.monitor), runs the test suite (python -m unittest discover -v), rebuilds the image with the trained model baked in, and starts the API container.
On success:
API: http://127.0.0.1:8000
Swagger docs: http://127.0.0.1:8000/docs
MLflow UI: http://127.0.0.1:5000
2. Simulate live traffic and generate monitoring dashboards
With the API running, in a separate step:
run_client.bat [count]
count defaults to 150 simulated requests. This sends simulated live requests (client.live_client), submits simulated feedback for accuracy tracking (client.feedback_client), computes accuracy-drift and data-drift reports (pipeline.accuracy_report, pipeline.drift_report), and builds two HTML dashboards which are opened automatically:
reports/dashboard.html
reports/observability_dashboard.html
Request/response traffic is logged to logs/client_requests.txt; drift and accuracy reports are written to reports/drift_table.md andreports/accuracy_drift.md.
3. Reset the demo
clean_demo.bat
Stops the MLflow container, clears mlruns/, logs/, experiments/,reports/, and artifacts/, and recreates the empty folders so run.batcan be run again from a clean state. The running API container is left untouched.
Testing
python -m unittest discover -v
This runs automatically as part of run.bat, after training and before the API image is rebuilt — the pipeline stops if tests fail.

