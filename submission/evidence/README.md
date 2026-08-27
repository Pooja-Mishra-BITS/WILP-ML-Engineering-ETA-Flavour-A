# Evidence capture guide

Do not fabricate screenshots. Capture the command, output, and date from the actual run. Store screenshots outside the final ZIP unless the instructor requests them; keep these Markdown instructions in the project.

Files:

- 01_data_validation.md: terminal output from python -m pipeline.validate and row counts.
- 02_dataset_versioning.md: data/VERSION, data/manifest.json, project-local Git root, and commits.
- 03_experiments.md: MLflow UI or mlflow runs output plus experiments/runs.jsonl.
- 04_model_comparison.md: reports/model_comparison.md and training output.
- 05_api.md: /health, valid trip /predict, empty payload, malformed JSON, and captured responses.
- 06_docker.md: docker build, docker run, and container endpoint responses.
- 07_monitoring.md: python -m pipeline.monitor output.
- 08_drift.md: data/simulated/drift_trips.csv and PSI/RMSE output.
- 09_retraining.md: threshold logic and retraining decision output.
