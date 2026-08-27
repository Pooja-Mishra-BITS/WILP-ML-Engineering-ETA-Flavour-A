# Delivery / Ride ETA Prediction — Flavor A

Machine Learning Engineering (PCAM* ZC412) mini-project. The system predicts delivery or ride duration in minutes from route coordinates, distance, time, weather, and traffic.

## Problem statement

Given trip metadata available when a ride or delivery is requested, estimate the expected trip duration. This project demonstrates ingestion, validation, reproducible regression experiments, model packaging, REST inference, logging, drift monitoring, and a documented retraining decision.

## Architecture

```text
data/raw/trips.csv -> validate.py -> data/processed/trips_clean.csv
                                      |
                                      v
                         train.py -> preprocessing -> MLflow runs -> reports/
                                      |
                                      v
                           FastAPI /predict -> logs/predictions.jsonl
                                      ^
                         monitor.py <- feedback + simulated drift
                                      |
                           detect -> trigger -> retrain workflow
```

## Repository structure

`pipeline/` contains generation, validation, features, training, and monitoring. `data/` contains deterministic raw, processed, and simulated datasets. `artifacts/` contains the selected joblib bundle. `experiments/` contains run summaries and a selected-model copy. `api/` contains FastAPI. `logs/`, `reports/`, `submission/evidence/`, and `tests/` contain operational outputs, documentation, evidence instructions, and automated tests.

## Dataset and validation

`pipeline.generate_data` creates 603 deterministic rows using seed 412: 600 valid trips and 3 intentionally malformed rows. Validation checks schema, numeric fields, coordinate bounds, positive distance/duration, valid time values, weather/traffic categories, and ISO timestamps. Accepted rows are written to `data/processed/trips_clean.csv`; rejected rows are quarantined in `data/processed/rejected_rows.jsonl`.

The dataset is synthetic and must not be presented as real-world performance. Continuous coordinates and varied trip conditions provide independent examples; the training report records the exact train/test feature-overlap check.

## Dataset versioning

`data/VERSION` stores the dataset version. `data/manifest.json` stores the seed, row counts, and SHA-256 hashes of raw and processed files, plus split sizes. Git history versions the pipeline and manifests. DVC is not required or claimed; the manifest-plus-Git approach is the documented equivalent.

## Features and experiments

The feature pipeline uses numeric features (coordinates, distance, hour, weekday) with `StandardScaler`, and categorical features (weather and traffic level) with `OneHotEncoder(handle_unknown="ignore")`. The `ColumnTransformer` is fitted only on the training partition and persisted inside `artifacts/model.joblib`; the API uses the same fitted pipeline.

Two actual local MLflow runs are created by `python -m pipeline.train`: linear regression and gradient boosting regression. Each logs parameters, seed, feature configuration, train/test sizes, MAE, RMSE, R², dataset version, and a metrics artifact. The selected model is the lowest held-out RMSE. Results are exported to `experiments/runs.jsonl` and `reports/model_comparison.md`.

Inspect local tracking after training with `mlflow ui --backend-store-uri ./mlruns --host 127.0.0.1 --port 5000`. The `mlruns/` directory is regenerated locally and excluded from the handoff ZIP.

## Reproducibility

Use Python 3.12 where possible. Dependencies are pinned in `requirements.txt`; parameters and seed are in `params.yaml`. From the project root, run training, monitoring, and tests in that order. Training saves a self-contained joblib bundle and the API does not retrain.

## Windows PowerShell setup

```powershell
cd C:\path\to\ml-engineering-mini-project
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pipeline.train
python -m pipeline.monitor
python -m unittest discover -v
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again. Keep the terminal in the project root.

## Mac/Linux setup

```bash
cd /path/to/ml-engineering-mini-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pipeline.train
python -m pipeline.monitor
python -m unittest discover -v
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

## REST API

`GET http://127.0.0.1:8000/health` returns service status and model version. `POST http://127.0.0.1:8000/predict` accepts JSON with `pickup_lat`, `pickup_lon`, `dropoff_lat`, `dropoff_lon`, `trip_distance_km`, `hour`, `weekday`, `weather`, and `traffic_level`.

Example request:

```json
{"pickup_lat":40.7,"pickup_lon":-73.9,"dropoff_lat":40.75,"dropoff_lon":-73.8,"trip_distance_km":8.5,"hour":17,"weekday":2,"weather":"rain","traffic_level":"high"}
```

The response contains `predicted_eta_minutes`, `model_version`, `latency_ms`, and `request_id`. Pydantic rejects missing, empty, out-of-range, and invalid categorical fields with HTTP 422. Malformed JSON also returns HTTP 422 with structured details. Actual tested responses are in `reports/api_test.md`.

## Docker

```bash
docker build -t ml-engineering-mini-project .
docker run --rm -p 8000:8000 ml-engineering-mini-project
```

Then test `/health` and `/predict`. Docker is only described as verified if the build and running-container checks succeed.

## Logging, monitoring, drift, and retraining

Successful predictions append structured JSONL to `logs/predictions.jsonl` with UTC timestamp, request ID, input hash, prediction, model version, and latency; raw input is not stored. Optional labelled feedback belongs in `logs/feedback.jsonl` using `logs/feedback.schema.json`.

`pipeline.monitor` separates production feedback from the reproducible assignment drift sample. The simulation creates 120 varied trips with longer routes, rush-hour demand, adverse weather, and festival/seasonal congestion. PSI on `trip_distance_km` compares a 480-row baseline with the 120-row drift sample; simulated labelled RMSE and MAE are also calculated. PSI depends on binning and sample size and is an alert signal, not proof of production failure.

Retraining is triggered when `PSI >= 0.20 OR drift RMSE > 8.0`. The action queues retraining; it does not launch a production job automatically. Intended workflow: `monitor -> detect -> trigger -> train -> validate -> promote`.

## Testing and reports

Run `python -m unittest discover -v`. The suite covers validation, artifact loading, API health/prediction/error handling, bounds, PSI, and train/test feature separation. Generated reports are in `reports/`; evidence capture instructions are in `submission/evidence/`.

## Assignment mapping

| Area | Implementation |
|---|---|
| Ingestion and validation | `pipeline/generate_data.py`, `pipeline/validate.py` |
| Features and experiments | `pipeline/features.py`, `pipeline/train.py`, local MLflow |
| Versioning and reproducibility | `data/VERSION`, `data/manifest.json`, `params.yaml`, Git |
| Model packaging | `artifacts/model.joblib`, `experiments/selected_model.joblib` |
| API and error handling | `api/server.py`, `tests/test_pipeline.py` |
| Logging and monitoring | `logs/`, `pipeline/monitor.py`, `reports/` |
| Deployment | `Dockerfile` |
| Evidence and demo | `reports/`, `submission/evidence/` |

## Limitations and references

The data is synthetic, the model does not use live map/road telemetry, PSI is sensitive to implementation choices, and production monitoring needs durable storage, alerts, and reliable labelled feedback. References: scikit-learn documentation, MLflow documentation, FastAPI documentation, and the course assignment brief.
