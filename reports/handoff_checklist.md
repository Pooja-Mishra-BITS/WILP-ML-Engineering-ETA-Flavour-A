# Flavor A handoff checklist

## A. Complete

- Flavor A Delivery / Ride ETA problem implemented.
- 603 raw rows generated; 600 accepted and 3 rejected by validation.
- Features include distance, hour, weekday, GPS coordinates, weather, and traffic.
- Deterministic seed 412 and 480/120 train/test split.
- Train/test feature overlap is 0.
- Linear regression and gradient boosting were actually trained and tracked in local MLflow.
- Selected joblib model is packaged at `artifacts/model.joblib`.
- FastAPI `/health` and `/predict` are tested, including validation failures.
- Docker image build and container endpoint checks succeeded.
- Prediction logging, monitoring, PSI drift detection, and queued retraining decision are implemented.
- README, reports, evidence instructions, and ZIP manifest are present.

## B. Still to do

- Pooja must create/use her own GitHub repository and remote.
- Pooja must capture any instructor-required screenshots and presentation/demo recording.
- Do not include `.git`, `.venv`, `mlruns`, caches, runtime JSONL logs, secrets, or unrelated files in the ZIP.

## C. Commands to run locally

```text
python -m pipeline.validate
python -m pipeline.train
python -m pipeline.monitor
python -m unittest discover -v
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

Docker:

```text
docker build -t ml-engineering-mini-project .
docker run --rm -p 8000:8000 ml-engineering-mini-project
```

## D. Include in ZIP

Include the files listed under `INCLUDE` in `reports/zip_manifest.txt`: source code, requirements, parameters, Docker files, data, model artifacts, reports, evidence instructions, and tests.

## E. Do not include

`.git/`, `.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`, `.env`, `mlruns/`, `experiments/artifacts/`, `logs/*.jsonl`, temporary files, credentials, parent-directory files, or unrelated projects.

## F. Pooja’s Windows commands after extraction

```powershell
cd C:\path\to\ml-engineering-mini-project
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pipeline.train
python -m pipeline.monitor
python -m unittest discover -v
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

## G. GitHub handoff

From the project root, Pooja should configure only her identity, initialize or continue her own repository, create a GitHub repository without an extra README, add her remote, and push `main`. The current project has no remote and no personal identity configuration was changed.
