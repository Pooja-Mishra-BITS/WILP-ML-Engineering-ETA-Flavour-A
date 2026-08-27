# Flavor A submission-readiness report

Audit date: 2026-08-27. Commands were run from the project root using the project-local environment. No GitHub remote was added and nothing was pushed.

## Verdict

READY TO HAND OFF. Docker image build and running-container endpoint checks have now succeeded.

## Verified results

- Dataset: 603 raw rows; 600 accepted; 3 rejected.
- Split: 480 train / 120 test; seed 412; exact feature-overlap count 0.
- Linear regression: MAE 3.8492, RMSE 4.8231, R2 0.9383.
- Gradient boosting: MAE 3.6173, RMSE 4.4615, R2 0.9472.
- Selected model: gradient_boosting by lowest held-out RMSE.
- MLflow: two actual local runs; run IDs are in `reports/training_report.json` and `experiments/runs.jsonl`.
- Artifact: `artifacts/model.joblib` loads and includes the fitted preprocessing pipeline and regressor.
- Monitoring: baseline 480, drift 120, PSI 3.248583, drift MAE 23.9021, drift RMSE 27.7416; retraining triggered because PSI and RMSE exceed thresholds.
- Tests: 8 discovered, 8 passed.
- API: health 200, valid prediction 200, empty payload 422, malformed JSON 422.
- Docker: image built successfully; running container returned health 200 and prediction 200.
- Security and portability: no project credentials found; source uses project-relative paths.

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| Versioned dataset and pipeline code | PASS | `data/VERSION`, `data/manifest.json`, `pipeline/` |
| GitHub/GitLab repository | PARTIAL | project-local Git root is ready; remote is intentionally not added |
| Meaningful incremental commit history | PASS | truthful local commits in project repository |
| Data ingestion | PASS | `pipeline/generate_data.py` |
| Data validation | PASS | `pipeline/validate.py`; 600 accepted/3 rejected |
| Feature engineering | PASS | scaled numeric and one-hot categorical `ColumnTransformer` |
| Dataset versioning | PASS | version file, SHA-256 manifest, Git |
| Two tracked ML experiments | PASS | two actual MLflow runs plus `experiments/runs.jsonl` |
| Model comparison with metrics | PASS | actual `reports/model_comparison.md` |
| Selected-model reproducibility | PASS | `params.yaml`, pinned requirements, seed 412 |
| Serialized/packageable best model | PASS | `artifacts/model.joblib` |
| REST API accepting trip input | PASS | `api/server.py` |
| Input/error validation | PASS | Pydantic bounds and actual 422 checks |
| API sample request/response | PASS | `reports/api_test.md` |
| Docker packaging/deployment | PASS | Actual build and container endpoint checks succeeded |
| Prediction logging | PASS | structured JSONL implementation and schema |
| Monitoring | PASS | separate prediction logs, feedback, simulation, calculations |
| Realistic drift simulation | PASS | varied 120-row trip simulation |
| Meaningful drift metrics | PASS | PSI, MAE, and RMSE with documented thresholds |
| Retraining trigger and logic | PASS | PSI/RMSE rule and queued action |
| README architecture diagram | PASS | Mermaid-like text architecture in `README.md` |
| README setup instructions | PASS | Windows and Mac/Linux commands |
| README design decisions | PASS | feature, model, monitoring, and limitation explanations |
| README assignment mapping | PASS | mapping table in `README.md` |
| Unit and API smoke tests | PASS | 8/8 via discovery and TestClient |
| Final report/evidence package | PASS | `reports/`, `submission/evidence/` |
| 5–7 minute demo readiness | PARTIAL | flow and evidence prompts exist; no recording is included |

## Remaining actions

1. Pooja should run the Windows commands in `README.md`, initialize her Git identity/remote from the project root, and push to her repository.
2. Capture instructor-facing screenshots listed in `submission/evidence/` without fabricating any output.
